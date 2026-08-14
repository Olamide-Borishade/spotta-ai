from logic.agents import ask_model


def test_say_hello():
    reply = ask_model("say hello")
    print("\nModel reply:", reply)
    assert isinstance(reply, str) and len(reply) > 0
