from app import chat as chat_mod


def test_file_list_not_shell_nl() -> None:
    assert chat_mod.is_file_list_intent("lista plikow usera")
    assert not chat_mod.is_shell_nl_intent("lista plikow usera")


def test_shell_nl_disk_intent() -> None:
    assert chat_mod.is_shell_nl_intent("sprawdz miejsce na dysku")


def test_run_prefix_not_shell_nl() -> None:
    assert not chat_mod.is_shell_nl_intent("run ls -la")
