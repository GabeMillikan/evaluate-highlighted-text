import bisect
import inspect
import time
from typing import Any, Callable, TypeAlias, overload

import keyboard
import pyperclip

Priority: TypeAlias = int | float
Transformer: TypeAlias = Callable[[Any], Any]
TransformerAdder: TypeAlias = Callable[[Transformer], int | float]
HotkeyRemover: TypeAlias = Any


class AllTransformersFailed(Exception):
    transformer_failures: dict[Transformer, Exception]
    input_text: str

    def __init__(
        self,
        input_text: str,
        transformer_failures: dict[Transformer, Exception],
    ) -> None:
        self.input_text = input_text
        self.transformer_failures = transformer_failures

        msg = (
            f"No transformers succeeded in processing the input: {input_text!r}\n"
            "Here are the errors they produced:\n"
        ) + "\n".join(f"    {t!r}: {e!r}" for t, e in transformer_failures.items())

        super().__init__(msg)


class Evaluator:
    hotkeys: dict[str, HotkeyRemover]
    transformers: list[tuple[Priority, Transformer, Any | None]]  # descending priority

    def __init__(self, *hotkeys: str) -> None:
        self.hotkeys = {
            key: keyboard.add_hotkey(
                key,
                self.run,
                suppress=True,
            )
            for key in hotkeys
        }
        self.transformers = []

    @staticmethod
    def extract_type_requirement(transformer: Transformer) -> Any | None:
        try:
            params = inspect.signature(transformer).parameters.values()
            annotation = next(iter(params)).annotation
            isinstance(123, annotation)
        except Exception:
            return None

        return annotation

    @overload
    def add(self) -> TransformerAdder: ...

    @overload
    def add(self, *, priority: Priority) -> TransformerAdder: ...

    @overload
    def add(self, transformer: Transformer) -> Priority: ...

    @overload
    def add(self, transformer: Transformer, *, priority: Priority) -> Priority: ...

    def add(
        self,
        transformer: Transformer | None = None,
        *,
        priority: Priority | None = None,
    ) -> TransformerAdder | Priority:
        def adder(transformer: Transformer) -> Priority:
            nonlocal priority

            if priority is None:
                if self.transformers:
                    priority = self.transformers[-1][0] - 1
                else:
                    priority = 0

            t = (
                priority,
                transformer,
                self.extract_type_requirement(transformer),
            )
            bisect.insort_right(self.transformers, t, key=lambda p: -p[0])

            return priority

        if transformer is not None:
            return adder(transformer)

        return adder

    def evaluate(self, text: str) -> Any:
        any_transformers_succeeded = False
        working_value: Any = text
        transformers = self.transformers.copy()

        transformer_failures: dict[Transformer, Exception] = {}

        while transformers:
            for i, (_priority, transformer, required_type) in enumerate(transformers):
                try:
                    if required_type and not isinstance(working_value, required_type):
                        msg = f"Not of required type {required_type!r}."
                        raise TypeError(msg)

                    working_value = transformer(working_value)
                except Exception as e:
                    transformer_failures[transformer] = e
                    continue  # try next one
                else:
                    any_transformers_succeeded = True
                    transformer_failures.pop(transformer, None)
                    del transformers[i]
                    break  # back to beginning
            else:
                # got through the whole list without a successful transformation
                break

        if any_transformers_succeeded:
            return working_value

        if transformer_failures:
            raise AllTransformersFailed(text, transformer_failures)

        return text

    def handle_failed_transformation(self, exc: AllTransformersFailed) -> None:
        # TODO: make this a callback
        print("All transformations failed.")
        print(exc)

    def get_highlighted_text(self) -> str:
        for hotkey in self.hotkeys:
            keyboard.release(hotkey)

        keyboard.press("ctrl+c")
        time.sleep(0.05)
        keyboard.release("ctrl+c")
        time.sleep(0.05)
        return pyperclip.paste()

    def write_text(self, text: str) -> None:
        keyboard.write(text, delay=0.001)

    def run(self) -> None:
        text = self.get_highlighted_text()
        try:
            transformed = self.evaluate(text)
        except AllTransformersFailed as e:
            self.handle_failed_transformation(e)
            return

        if not isinstance(transformed, str):
            transformed = repr(transformed)

        if transformed != text:
            self.write_text(transformed)

    def stop(self) -> None:
        for remover in self.hotkeys.values():
            keyboard.remove_hotkey(remover)
        self.hotkeys.clear()

    def wait(self) -> None:
        try:
            keyboard.wait()
        finally:
            self.stop()


__all__ = ["Evaluator"]
