class Semester:
    def __init__(self, enum_name: str, value: str) -> None:
        self.enum_name = enum_name
        self.value = value

    def __str__(self) -> str:
        return self.value

    def enum(self) -> str:
        return self.enum_name


class Fall(Semester):
    def __init__(self) -> None:
        super().__init__('F', '08')


class Summer(Semester):
    def __init__(self) -> None:
        super().__init__('X', '05')


class Spring(Semester):
    def __init__(self) -> None:
        super().__init__('S', '02')


FALL = Fall()
SUMMER = Summer()
SPRING = Spring()


def get_semester(semester_raw: str):
    semester_raw = semester_raw.lower()
    if semester_raw in ("s", "spring"):
        return SPRING

    if semester_raw in ("f", "fall"):
        return FALL

    if semester_raw in ("x", "summer"):
        return SUMMER

    return None
