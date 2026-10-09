"""Messages about a drawn helping line that does not follow the object it should trace."""

FAIL_TXT = {
    "line_hug": "the drawn line does not stay on the %s -- part of it runs off the thing it is "
                "supposed to be measuring",
    "line_ends": "the drawn line does not reach both ends of the %s -- it stops short of an end "
                 "or overshoots one",
}


FAIL_TXT["line_contact"] = (
    "the drawn line does not touch the %s at all -- it lies somewhere else in the picture")
