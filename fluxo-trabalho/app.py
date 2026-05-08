import streamlit as st
import json
import os
import base64
import html
from datetime import date, datetime
from supabase import create_client

st.set_page_config(page_title="TaskFlow", layout="wide")

ARQUIVO_TAREFAS = "tarefas.json"
ARQUIVO_PERFIS = "perfis.json"

STATUS = ["A Fazer", "Em Andamento", "Em Revisão", "Concluído"]
STATUS_ATIVOS = ["A Fazer", "Em Andamento", "Em Revisão"]
PRIORIDADES = ["Urgente", "Alta", "Média", "Baixa"]

ICONES = {
    "Urgente": "🔴",
    "Alta": "🟠",
    "Média": "🟡",
    "Baixa": "🔵"
}

PESO_PRIORIDADE = {
    "Urgente": 1,
    "Alta": 2,
    "Média": 3,
    "Baixa": 4
}


def carregar_css():
    if os.path.exists("style.css"):
        with open("style.css", "r", encoding="utf-8") as arquivo:
            st.markdown(f"<style>{arquivo.read()}</style>", unsafe_allow_html=True)


carregar_css()


TOKENS_CSV_URL = "https://docs.google.com/spreadsheets/d/1Uwav3x9hP9gk7eu8Gup-KJU-aerkdf6riWlht609MGk/edit?usp=sharing"


def carregar_json(arquivo):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def salvar_json(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)


def carregar_tarefas():
    return carregar_json(ARQUIVO_TAREFAS)


def salvar_tarefas():
    salvar_json(ARQUIVO_TAREFAS, st.session_state.tarefas)


def carregar_perfis():
    return carregar_json(ARQUIVO_PERFIS)


def salvar_perfis(perfis):
    salvar_json(ARQUIVO_PERFIS, perfis)


def data_valida(texto):
    try:
        return datetime.strptime(texto, "%Y-%m-%d").date()
    except:
        return None


def corrigir_tarefa(tarefa):
    prioridade = tarefa.get("prioridade", "Baixa")
    status = tarefa.get("status", "A Fazer")

    if prioridade not in PRIORIDADES:
        prioridade = "Baixa"

    if status not in STATUS:
        status = "A Fazer"

    return {
        "nome": tarefa.get("nome", "Sem nome"),
        "responsavel": tarefa.get("responsavel", ""),
        "descricao": tarefa.get("descricao", ""),
        "prioridade": prioridade,
        "prazo": tarefa.get("prazo", ""),
        "hora": tarefa.get("hora", ""),
        "status": status,
        "criado_por": tarefa.get("criado_por", "")
    }


def garantir_perfil(email):
    perfis = carregar_perfis()

    for perfil in perfis:
        if perfil.get("email") == email:
            return perfil

    novo = {
        "email": email,
        "nome": email.split("@")[0],
        "foto": "",
        "foto_tipo": "image/png"
    }

    perfis.append(novo)
    salvar_perfis(perfis)
    return novo


def buscar_perfil(email):
    perfis = carregar_perfis()

    for perfil in perfis:
        if perfil.get("email") == email:
            return perfil

    return garantir_perfil(email)


def atualizar_perfil(email, nome, foto_base64=None, foto_tipo=None):
    perfis = carregar_perfis()
    encontrado = False

    for perfil in perfis:
        if perfil.get("email") == email:
            perfil["nome"] = nome

            if foto_base64 is not None:
                perfil["foto"] = foto_base64

            if foto_tipo is not None:
                perfil["foto_tipo"] = foto_tipo

            encontrado = True

    if not encontrado:
        perfis.append({
            "email": email,
            "nome": nome,
            "foto": foto_base64 or "",
            "foto_tipo": foto_tipo or "image/png"
        })

    salvar_perfis(perfis)


def nomes_usuarios():
    perfis = carregar_perfis()
    nomes = []

    for perfil in perfis:
        nome = perfil.get("nome") or perfil.get("email")
        if nome and nome not in nomes:
            nomes.append(nome)

    return sorted(nomes)


def nome_do_usuario_logado():
    perfil = buscar_perfil(st.session_state.usuario_email)
    return perfil.get("nome") or st.session_state.usuario_email


def ir_para(pagina):
    st.query_params["pagina"] = pagina
    st.rerun()


def mostrar_avatar():
    perfil = buscar_perfil(st.session_state.usuario_email)
    nome = html.escape(perfil.get("nome") or st.session_state.usuario_email)

    if perfil.get("foto"):
        src = f"data:{perfil.get('foto_tipo', 'image/png')};base64,{perfil['foto']}"

        st.markdown(
            f"""
            <a href="?pagina=Perfil" class="avatar-link">
                <img src="{src}" class="avatar-img">
                <div class="avatar-name">{nome}</div>
            </a>
            """,
            unsafe_allow_html=True
        )
    else:
        letra = nome[:1].upper()

        st.markdown(
            f"""
            <a href="?pagina=Perfil" class="avatar-link">
                <div class="avatar-fallback">{letra}</div>
                <div class="avatar-name">{nome}</div>
            </a>
            """,
            unsafe_allow_html=True
        )


if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario_email" not in st.session_state:
    st.session_state.usuario_email = ""


def pegar_email_usuario(resposta):
    try:
        if resposta.user and resposta.user.email:
            return resposta.user.email
    except:
        pass

    try:
        if resposta.session and resposta.session.user and resposta.session.user.email:
            return resposta.session.user.email
    except:
        pass

    try:
        usuario = supabase.auth.get_user()
        if usuario and usuario.user and usuario.user.email:
            return usuario.user.email
    except:
        pass

    return ""


def processar_retorno_google():
    if st.session_state.logado:
        return

    codigo = st.query_params.get("code", "")

    if not codigo:
        return

    try:
        resposta = supabase.auth.exchange_code_for_session({
            "auth_code": codigo
        })

        email = pegar_email_usuario(resposta)

        if email:
            st.session_state.logado = True
            st.session_state.usuario_email = email
            garantir_perfil(email)
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Login Google voltou, mas não consegui identificar o e-mail.")

    except Exception as erro:
        st.error("Não foi possível concluir o login com Google.")
        st.exception(erro)


processar_retorno_google()


def tela_login():
    centro1, centro2, centro3 = st.columns([1, 1.25, 1])

    with centro2:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown("## TaskFlow")
        st.caption("Sistema visual de gestão de tarefas")

        app_url = st.secrets.get("APP_URL", "")

        if st.button("Entrar com Google", use_container_width=True):
            try:
                resposta = supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {
                        "redirect_to": app_url
                    }
                })

                if resposta.url:
                    st.markdown(
                        f"""
                        <meta http-equiv="refresh" content="0; url={resposta.url}">
                        <a href="{resposta.url}">Clique aqui se não redirecionar automaticamente</a>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.error("Não foi possível gerar o link do Google.")

            except Exception as erro:
                st.error("Erro ao iniciar login com Google.")
                st.exception(erro)

        st.divider()

        aba_login, aba_cadastro, aba_reset = st.tabs(
            ["Entrar", "Criar conta", "Recuperar senha"]
        )

        with aba_login:
            email = st.text_input("E-mail", key="login_email")
            senha = st.text_input("Senha", type="password", key="login_senha")

            if st.button("Entrar", key="btn_login", use_container_width=True):
                try:
                    resposta = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": senha
                    })

                    email_usuario = pegar_email_usuario(resposta)

                    if email_usuario:
                        st.session_state.logado = True
                        st.session_state.usuario_email = email_usuario
                        garantir_perfil(email_usuario)
                        st.rerun()
                    else:
                        st.error("Não foi possível entrar.")

                except Exception:
                    st.error("E-mail ou senha inválidos.")

        with aba_cadastro:
            email = st.text_input("E-mail", key="cad_email")
            senha = st.text_input("Senha", type="password", key="cad_senha")
            confirmar = st.text_input("Confirmar senha", type="password", key="cad_confirmar")
            nome = st.text_input("Nome de exibição", key="cad_nome")

            if st.button("Criar conta", key="btn_cadastro", use_container_width=True):
                if senha != confirmar:
                    st.error("As senhas não coincidem.")
                elif not email.strip():
                    st.error("Digite um e-mail.")
                elif not senha.strip():
                    st.error("Digite uma senha.")
                else:
                    try:
                        supabase.auth.sign_up({
                            "email": email,
                            "password": senha
                        })

                        nome_final = nome.strip() or email.split("@")[0]
                        atualizar_perfil(email, nome_final)

                        st.success("Conta criada. Agora tente entrar.")

                    except Exception as erro:
                        st.error("Não foi possível criar a conta.")
                        st.exception(erro)

        with aba_reset:
            email_reset = st.text_input("E-mail da conta", key="reset_email")

            if st.button("Enviar recuperação", key="btn_reset", use_container_width=True):
                try:
                    supabase.auth.reset_password_for_email(email_reset)
                    st.success("Se o e-mail existir, você receberá a recuperação.")
                except Exception:
                    st.error("Não foi possível enviar recuperação.")

        st.markdown("</div>", unsafe_allow_html=True)


if not st.session_state.logado:
    tela_login()
    st.stop()


if "tarefas" not in st.session_state:
    tarefas = carregar_tarefas()
    st.session_state.tarefas = [corrigir_tarefa(t) for t in tarefas]
    salvar_tarefas()


pagina_url = st.query_params.get("pagina", "Quadro")

if pagina_url not in ["Quadro", "Concluídas", "Perfil"]:
    pagina_url = "Quadro"


topo1, topo2, topo3 = st.columns([5, 2, 1])

with topo1:
    st.markdown("# TaskFlow")
    st.caption("Painel profissional de gestão de tarefas")

with topo2:
    st.write("")
    if st.button("Sair", use_container_width=True):
        st.session_state.logado = False
        st.session_state.usuario_email = ""
        st.query_params.clear()
        st.rerun()

with topo3:
    mostrar_avatar()


with st.sidebar:
    st.markdown("## Menu")

    if st.button("📋 Quadro", use_container_width=True):
        ir_para("Quadro")

    if st.button("✅ Concluídas", use_container_width=True):
        ir_para("Concluídas")

    st.caption("Clique na foto no topo para abrir o perfil.")

    st.divider()

    if pagina_url == "Quadro":
        st.header("Nova tarefa")

        lista_usuarios = nomes_usuarios()

        with st.form("form_tarefa"):
            nome = st.text_input("Nome da tarefa")

            if lista_usuarios:
                responsavel = st.selectbox("Responsável", lista_usuarios)
            else:
                responsavel = nome_do_usuario_logado()

            descricao = st.text_area("Descrição")
            prioridade = st.selectbox("Prioridade", PRIORIDADES)
            prazo = st.date_input("Prazo", date.today())
            hora = st.time_input("Hora")

            criar = st.form_submit_button("Criar tarefa")

            if criar:
                if nome.strip() == "":
                    st.error("Digite o nome da tarefa.")
                else:
                    st.session_state.tarefas.append({
                        "nome": nome,
                        "responsavel": responsavel,
                        "descricao": descricao,
                        "prioridade": prioridade,
                        "prazo": str(prazo),
                        "hora": str(hora),
                        "status": "A Fazer",
                        "criado_por": nome_do_usuario_logado()
                    })

                    salvar_tarefas()
                    st.rerun()

        st.divider()

        st.header("Filtros")
        pesquisa = st.text_input("Pesquisar")
        filtro_status = st.selectbox("Status", ["Todos"] + STATUS_ATIVOS)
        filtro_prioridade = st.selectbox("Prioridade", ["Todas"] + PRIORIDADES)

    elif pagina_url == "Concluídas":
        st.header("Filtros avançados")

        pesquisa_concluidas = st.text_input("Pesquisar")
        responsavel_concluidas = st.selectbox("Responsável", ["Todos"] + nomes_usuarios())
        criador_concluidas = st.selectbox("Criado por", ["Todos"] + nomes_usuarios())

        prioridade_concluidas = st.multiselect(
            "Prioridades",
            PRIORIDADES,
            default=PRIORIDADES
        )

        ordenar_concluidas = st.selectbox(
            "Ordenar por",
            [
                "Prioridade",
                "Prazo mais próximo",
                "Prazo mais distante",
                "Nome A-Z",
                "Responsável A-Z"
            ]
        )

        st.write("Período do prazo")

        data_inicio_concluidas = st.date_input(
            "De",
            value=date(2020, 1, 1),
            key="data_inicio_concluidas"
        )

        data_fim_concluidas = st.date_input(
            "Até",
            value=date.today(),
            key="data_fim_concluidas"
        )

    else:
        st.info("Perfil aberto pela foto.")


if pagina_url == "Quadro":
    tarefas_ativas = [
        t for t in st.session_state.tarefas
        if t["status"] != "Concluído"
    ]

    st.subheader("Resumo")

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Ativas", len(tarefas_ativas))
    m2.metric("A Fazer", len([t for t in tarefas_ativas if t["status"] == "A Fazer"]))
    m3.metric("Em Andamento", len([t for t in tarefas_ativas if t["status"] == "Em Andamento"]))
    m4.metric("Em Revisão", len([t for t in tarefas_ativas if t["status"] == "Em Revisão"]))

    st.info("Prioridade no topo: Urgente → Alta → Média → Baixa.")

    st.divider()
    st.subheader("Quadro de tarefas")

    col1, col2, col3 = st.columns(3)

    colunas = {
        "A Fazer": col1,
        "Em Andamento": col2,
        "Em Revisão": col3
    }

    for nome_status, coluna in colunas.items():
        with coluna:
            tarefas_da_coluna = [
                (i, t)
                for i, t in enumerate(st.session_state.tarefas)
                if t["status"] == nome_status
            ]

            tarefas_da_coluna = sorted(
                tarefas_da_coluna,
                key=lambda item: PESO_PRIORIDADE.get(item[1]["prioridade"], 99)
            )

            st.markdown(f"### {nome_status} ({len(tarefas_da_coluna)})")

            mostradas = 0

            for i, tarefa in tarefas_da_coluna:
                texto = (
                    tarefa["nome"] +
                    tarefa["responsavel"] +
                    tarefa["descricao"]
                ).lower()

                if pesquisa.lower() not in texto:
                    continue

                if filtro_status != "Todos" and tarefa["status"] != filtro_status:
                    continue

                if filtro_prioridade != "Todas" and tarefa["prioridade"] != filtro_prioridade:
                    continue

                mostradas += 1
                icone = ICONES.get(tarefa["prioridade"], "⚪")

                with st.container(border=True):
                    st.markdown(f"#### {icone} {tarefa['nome']}")

                    with st.expander("Abrir tarefa"):
                        st.write(f"**Responsável:** {tarefa['responsavel']}")
                        st.write(f"**Prioridade:** {tarefa['prioridade']}")
                        st.write(f"**Prazo:** {tarefa['prazo']}")
                        st.write(f"**Hora:** {tarefa['hora']}")
                        st.write(f"**Criado por:** {tarefa.get('criado_por', '')}")

                        if tarefa["descricao"]:
                            st.write("**Descrição:**")
                            st.write(tarefa["descricao"])

                    indice_atual = STATUS.index(tarefa["status"])
                    proximo_status = STATUS[indice_atual + 1]

                    if st.button(
                        f"Avançar para {proximo_status}",
                        key=f"avancar_{i}",
                        use_container_width=True
                    ):
                        st.session_state.tarefas[i]["status"] = proximo_status
                        salvar_tarefas()
                        st.rerun()

                    with st.expander("Editar"):
                        novo_nome = st.text_input("Nome", value=tarefa["nome"], key=f"nome_{i}")
                        lista_resp = nomes_usuarios()

                        if tarefa["responsavel"] in lista_resp:
                            indice_resp = lista_resp.index(tarefa["responsavel"])
                        else:
                            indice_resp = 0

                        novo_responsavel = st.selectbox(
                            "Responsável",
                            lista_resp,
                            index=indice_resp,
                            key=f"resp_{i}"
                        )

                        nova_descricao = st.text_area("Descrição", value=tarefa["descricao"], key=f"desc_{i}")

                        nova_prioridade = st.selectbox(
                            "Prioridade",
                            PRIORIDADES,
                            index=PRIORIDADES.index(tarefa["prioridade"]),
                            key=f"prio_{i}"
                        )

                        novo_prazo = st.text_input("Prazo", value=tarefa["prazo"], key=f"prazo_{i}")
                        nova_hora = st.text_input("Hora", value=tarefa["hora"], key=f"hora_{i}")

                        if st.button("Salvar edição", key=f"salvar_{i}", use_container_width=True):
                            st.session_state.tarefas[i]["nome"] = novo_nome
                            st.session_state.tarefas[i]["responsavel"] = novo_responsavel
                            st.session_state.tarefas[i]["descricao"] = nova_descricao
                            st.session_state.tarefas[i]["prioridade"] = nova_prioridade
                            st.session_state.tarefas[i]["prazo"] = novo_prazo
                            st.session_state.tarefas[i]["hora"] = nova_hora
                            salvar_tarefas()
                            st.rerun()

                    if st.button("Excluir", key=f"excluir_{i}", use_container_width=True):
                        st.session_state.tarefas.pop(i)
                        salvar_tarefas()
                        st.rerun()

            if mostradas == 0:
                st.info("Nenhuma tarefa")


elif pagina_url == "Concluídas":
    st.subheader("Tarefas concluídas")

    concluidas = [
        (i, t)
        for i, t in enumerate(st.session_state.tarefas)
        if t["status"] == "Concluído"
    ]

    filtradas = []

    for i, tarefa in concluidas:
        texto = (
            tarefa["nome"] +
            tarefa["responsavel"] +
            tarefa["descricao"] +
            tarefa.get("criado_por", "")
        ).lower()

        if pesquisa_concluidas.lower() not in texto:
            continue

        if responsavel_concluidas != "Todos" and tarefa["responsavel"] != responsavel_concluidas:
            continue

        if criador_concluidas != "Todos" and tarefa.get("criado_por", "") != criador_concluidas:
            continue

        if tarefa["prioridade"] not in prioridade_concluidas:
            continue

        prazo_data = data_valida(tarefa.get("prazo", ""))

        if prazo_data:
            if prazo_data < data_inicio_concluidas or prazo_data > data_fim_concluidas:
                continue

        filtradas.append((i, tarefa))

    if ordenar_concluidas == "Prioridade":
        filtradas = sorted(filtradas, key=lambda item: PESO_PRIORIDADE.get(item[1]["prioridade"], 99))
    elif ordenar_concluidas == "Prazo mais próximo":
        filtradas = sorted(filtradas, key=lambda item: data_valida(item[1].get("prazo", "")) or date.max)
    elif ordenar_concluidas == "Prazo mais distante":
        filtradas = sorted(filtradas, key=lambda item: data_valida(item[1].get("prazo", "")) or date.min, reverse=True)
    elif ordenar_concluidas == "Nome A-Z":
        filtradas = sorted(filtradas, key=lambda item: item[1]["nome"].lower())
    elif ordenar_concluidas == "Responsável A-Z":
        filtradas = sorted(filtradas, key=lambda item: item[1]["responsavel"].lower())

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Resultado", len(filtradas))
    c2.metric("Urgentes", len([t for _, t in filtradas if t["prioridade"] == "Urgente"]))
    c3.metric("Altas", len([t for _, t in filtradas if t["prioridade"] == "Alta"]))
    c4.metric("Médias/Baixas", len([t for _, t in filtradas if t["prioridade"] in ["Média", "Baixa"]]))

    st.divider()

    for i, tarefa in filtradas:
        icone = ICONES.get(tarefa["prioridade"], "⚪")

        with st.container(border=True):
            st.markdown(f"#### {icone} {tarefa['nome']}")

            with st.expander("Abrir tarefa concluída"):
                st.write(f"**Responsável:** {tarefa['responsavel']}")
                st.write(f"**Prioridade:** {tarefa['prioridade']}")
                st.write(f"**Prazo:** {tarefa['prazo']}")
                st.write(f"**Hora:** {tarefa['hora']}")
                st.write(f"**Criado por:** {tarefa.get('criado_por', '')}")

                if tarefa["descricao"]:
                    st.write("**Descrição:**")
                    st.write(tarefa["descricao"])

            st.success("Concluída")

    if len(filtradas) == 0:
        st.info("Nenhuma tarefa concluída encontrada.")


elif pagina_url == "Perfil":
    st.subheader("Perfil")

    perfil = buscar_perfil(st.session_state.usuario_email)

    perfil_col1, perfil_col2 = st.columns([1, 3])

    with perfil_col1:
        if perfil.get("foto"):
            bytes_foto = base64.b64decode(perfil["foto"])
            st.image(bytes_foto, width=128)
        else:
            st.info("Sem foto")

    with perfil_col2:
        novo_nome = st.text_input("Nome de exibição", value=perfil.get("nome", ""))
        st.caption(f"E-mail: {st.session_state.usuario_email}")
        st.info("A imagem ou GIF precisa ter exatamente 128x128 pixels.")

        arquivo_foto = st.file_uploader(
            "Enviar foto/GIF 128x128 pixels",
            type=["png", "jpg", "jpeg", "gif"]
        )

        foto_base64 = None
        foto_tipo = None

        if arquivo_foto is not None:
            dados = arquivo_foto.read()
            foto_base64 = base64.b64encode(dados).decode("utf-8")
            foto_tipo = arquivo_foto.type

            st.image(dados, width=128)
            st.caption("Prévia 128x128 pixels.")

        if st.button("Salvar perfil", use_container_width=True):
            atualizar_perfil(
                st.session_state.usuario_email,
                novo_nome,
                foto_base64,
                foto_tipo
            )
            st.success("Perfil salvo.")
            st.rerun()
