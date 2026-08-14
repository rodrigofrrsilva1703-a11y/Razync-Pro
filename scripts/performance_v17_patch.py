from pathlib import Path

p = Path('app.py')
s = p.read_text(encoding='utf-8')

s = s.replace('progress = onboarding_progress(get_profile(uid), not transactions.empty, bool(das_rows), bool(docs))', 'progress = onboarding_progress(profile, not transactions.empty, bool(das_rows), bool(docs))')
s = s.replace('for tip in recommended_setup(get_profile(uid)):', 'for tip in recommended_setup(profile):')

old_docs = '''        did=st.selectbox("Abrir documento",[d["id"] for d in docs],format_func=lambda x:next(d["filename"] for d in docs if d["id"]==x))
        selected=get_document(uid,int(did))
        if selected:
            try:
                content = document_bytes(selected)
            except Exception:
                st.error("Não foi possível baixar o documento agora.")
            else:
                st.download_button(
                    "Baixar arquivo", content, file_name=selected["filename"],
                    mime=selected["mime_type"] or "application/octet-stream",
                    use_container_width=True,
                )
        with st.expander("Excluir documento"):
            st.caption("A exclusão remove o arquivo armazenado no Razync.")
            if st.button("Excluir documento selecionado",use_container_width=True):
                try:
                    remove_saved_document(uid, selected)
                except Exception:
                    st.error("Não foi possível excluir o documento agora.")
                else:
                    st.rerun()
'''
new_docs = '''        did=st.selectbox("Abrir documento",[d["id"] for d in docs],format_func=lambda x:next(d["filename"] for d in docs if d["id"]==x))
        selected_meta = next(d for d in docs if int(d["id"]) == int(did))
        prepared_key = f"_prepared_document_{uid}_{int(did)}"
        if st.button("Preparar arquivo para download", key=f"prepare_doc_{did}", use_container_width=True):
            try:
                selected = get_document(uid,int(did))
                if not selected:
                    raise RuntimeError("Documento não encontrado")
                content = document_bytes(selected)
            except Exception:
                st.error("Não foi possível baixar o documento agora.")
            else:
                st.session_state[prepared_key] = {
                    "content": content,
                    "filename": selected["filename"],
                    "mime_type": selected["mime_type"] or "application/octet-stream",
                }
        prepared_document = st.session_state.get(prepared_key)
        if prepared_document:
            st.download_button(
                "Baixar arquivo",
                prepared_document["content"],
                file_name=prepared_document["filename"],
                mime=prepared_document["mime_type"],
                use_container_width=True,
            )
        with st.expander("Excluir documento"):
            st.caption("A exclusão remove o arquivo armazenado no Razync.")
            if st.button("Excluir documento selecionado",use_container_width=True):
                try:
                    remove_saved_document(uid, selected_meta)
                except Exception:
                    st.error("Não foi possível excluir o documento agora.")
                else:
                    st.session_state.pop(prepared_key, None)
                    st.rerun()
'''
if old_docs not in s:
    raise SystemExit('document block not found')
s = s.replace(old_docs, new_docs, 1)

old_backup = '''elif page == "Backup":
    header("Backup","Baixe um pacote dos dados para manter uma cópia independente.")
    backup=build_backup_zip(profile,transactions,invoices,das_rows,obligations,contacts,employees,docs,lambda doc_id:(lambda d: {**d, "content": document_bytes(d)} if d else None)(get_document(uid,doc_id)))
    st.download_button("Baixar backup completo (.zip)",backup,file_name=f"backup_razync_{date.today().isoformat()}.zip",mime="application/zip",use_container_width=True)
    st.caption("O pacote inclui dados em CSV/JSON, manifesto e os documentos disponíveis no Razync Pro.")
    st.code(backup_checksum(backup), language=None)
    st.caption("Guarde este código de integridade junto do arquivo para conferir se o backup não foi alterado.")
'''
new_backup = '''elif page == "Backup":
    header("Backup","Baixe um pacote dos dados para manter uma cópia independente.")
    backup_key = f"_prepared_backup_{uid}_{_current_data_version}"
    st.caption("O backup é preparado somente quando você solicitar, evitando carregar todos os documentos ao abrir esta página.")
    if st.button("Preparar backup completo", type="primary", use_container_width=True):
        with st.spinner("Preparando backup..."):
            backup = build_backup_zip(
                profile, transactions, invoices, das_rows, obligations, contacts, employees, docs,
                lambda doc_id:(lambda d: {**d, "content": document_bytes(d)} if d else None)(get_document(uid,doc_id)),
            )
            st.session_state[backup_key] = backup
    backup = st.session_state.get(backup_key)
    if backup:
        st.download_button("Baixar backup completo (.zip)",backup,file_name=f"backup_razync_{date.today().isoformat()}.zip",mime="application/zip",use_container_width=True)
        st.caption("O pacote inclui dados em CSV/JSON, manifesto e os documentos disponíveis no Razync Pro.")
        st.code(backup_checksum(backup), language=None)
        st.caption("Guarde este código de integridade junto do arquivo para conferir se o backup não foi alterado.")
'''
if old_backup not in s:
    raise SystemExit('backup block not found')
s = s.replace(old_backup, new_backup, 1)

p.write_text(s, encoding='utf-8')
print('Performance V17 aplicada: leituras remotas de documentos, backup e perfil agora sao sob demanda/snapshot.')
