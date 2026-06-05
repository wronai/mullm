from app.local_orient import orient_query


def test_lista_plikow_usera_host():
    o = orient_query("lista plikow usera")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /host-home"
    assert "orientation_path_host_home" in o.reason_codes


def test_lista_plikow_github_path_hint():
    o = orient_query("lista plikow github")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /host-home/github"
    assert o.list_scope == "github"
    assert "orientation_path_hint_github" in o.reason_codes


def test_registry_hint():
    o = orient_query("lista plikow usera z rejestru")
    assert o.category == "file_list_registry"
    assert o.suggested_action == "mullm_list_files"


def test_lista_plikow_systemu_root_fs():
    o = orient_query("lista plikow systemu")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /"
    assert o.list_scope == "system"
    assert "orientation_path_system_root" in o.reason_codes


def test_lista_plikow_linux_host_home():
    o = orient_query("lista plikow linux")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /host-home"
    assert o.list_scope == "host"
    assert "orientation_path_host_home" in o.reason_codes


def test_lista_plikow_root_slash():
    o = orient_query("lista plikow /")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /"
    assert "orientation_path_root" in o.reason_codes


def test_lista_plikow_projektu_nlp2cmd():
    o = orient_query("lista plikow projektu nlp2cmd")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /host-home/github/wronai/nlp2cmd"
    assert o.list_scope == "nlp2cmd"
    assert "orientation_path_project_nlp2cmd" in o.reason_codes


def test_lista_plikow_w_github_multi_segment():
    o = orient_query("lista plikow w github wronai nlp2cmd")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /host-home/github/wronai/nlp2cmd"
    assert "orientation_path_hint_github_wronai_nlp2cmd" in o.reason_codes


def test_lista_plikow_projektu_only():
    o = orient_query("lista plikow projektu")
    assert o.category == "file_list_host"
    assert o.shell_command == "ls -la /host-home/github"
    assert "orientation_path_projects" in o.reason_codes


def test_jspaint_orient_nlp2cmd_run():
    o = orient_query("wejdz na jspaint.app i narysuj biedronke")
    assert o.category == "shell"
    assert o.shell_command is None
    assert "orientation_nlp2cmd_run" in o.reason_codes
