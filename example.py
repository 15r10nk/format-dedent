import textwrap

l = [
    1,
    textwrap.dedent(
        """
SELECT *

FROM users    \n\
WHERE active = true
    AND age > 18
"""
    ),
    2,
    3,
]
