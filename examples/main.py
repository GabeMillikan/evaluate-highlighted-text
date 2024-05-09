import evaluate_highlighted_text as eht

evaluator = eht.Evaluator("ctrl+shift+e")

evaluator.add(eht.defaults.math)
evaluator.add(eht.defaults.formatting)

print("Running!")
evaluator.wait()
