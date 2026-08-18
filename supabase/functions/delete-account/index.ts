import { createClient } from "npm:@supabase/supabase-js@2";

function envKey(name: string, legacyName: string): string {
  const modern = Deno.env.get(name);
  if (modern) {
    try {
      const parsed = JSON.parse(modern);
      if (parsed && typeof parsed.default === "string") return parsed.default;
    } catch (_) {
      // Some environments may expose a single value instead of a named map.
      if (modern.startsWith("sb_")) return modern;
    }
  }
  return Deno.env.get(legacyName) || "";
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return Response.json({ error: "Método não permitido." }, { status: 405 });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL") || "";
  const publishableKey = envKey("SUPABASE_PUBLISHABLE_KEYS", "SUPABASE_ANON_KEY");
  const secretKey = envKey("SUPABASE_SECRET_KEYS", "SUPABASE_SERVICE_ROLE_KEY");
  const authorization = req.headers.get("Authorization") || "";

  if (!supabaseUrl || !publishableKey || !secretKey || !authorization.startsWith("Bearer ")) {
    return Response.json({ error: "Configuração de segurança indisponível." }, { status: 500 });
  }

  const token = authorization.slice("Bearer ".length).trim();
  const userClient = createClient(supabaseUrl, publishableKey, {
    global: { headers: { Authorization: `Bearer ${token}` } },
    auth: { persistSession: false, autoRefreshToken: false },
  });
  const admin = createClient(supabaseUrl, secretKey, {
    auth: { persistSession: false, autoRefreshToken: false },
  });

  const { data: authData, error: authError } = await userClient.auth.getUser(token);
  const authUser = authData?.user;
  if (authError || !authUser) {
    return Response.json({ error: "Sessão inválida ou expirada." }, { status: 401 });
  }

  try {
    // Storage paths are flat under <auth_user_id>/, as created by storage_service.py.
    let offset = 0;
    const paths: string[] = [];
    while (true) {
      const { data: objects, error: listError } = await admin.storage
        .from("documents")
        .list(authUser.id, { limit: 100, offset, sortBy: { column: "name", order: "asc" } });
      if (listError) throw listError;
      const rows = objects || [];
      for (const item of rows) {
        if (item.name) paths.push(`${authUser.id}/${item.name}`);
      }
      if (rows.length < 100) break;
      offset += rows.length;
    }
    if (paths.length) {
      const { error: removeError } = await admin.storage.from("documents").remove(paths);
      if (removeError) throw removeError;
    }

    // All business tables reference public.users with ON DELETE CASCADE.
    const { error: businessDeleteError } = await admin
      .from("users")
      .delete()
      .eq("auth_user_id", authUser.id);
    if (businessDeleteError) throw businessDeleteError;

    const { error: authDeleteError } = await admin.auth.admin.deleteUser(authUser.id, false);
    if (authDeleteError) throw authDeleteError;

    return Response.json({ deleted: true }, { status: 200 });
  } catch (error) {
    console.error(JSON.stringify({ event: "account_delete_failed", error_type: error?.constructor?.name || "Error" }));
    return Response.json(
      { error: "Não foi possível concluir a exclusão. Nenhuma credencial administrativa foi exposta." },
      { status: 500 },
    );
  }
});
