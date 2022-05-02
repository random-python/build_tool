"""
"""


import os

from build_tool.persist_attr import PersistAttr

this_dir = os.path.dirname(__file__)
test_dir = f"{this_dir}/test.dir"


def test_attr():
    print()

    key = "hello-kitty"

    file_path = f"{test_dir}/attr-file.md"

    os.makedirs(test_dir, exist_ok=True)
    with open(file_path, "w+") as file_hand:
        file_hand.write("hello-kitty")


    target = PersistAttr.extract_json(key, file_path)
    assert target is None

    source = dict(
        index=1,
        entry_list=[
            dict(
                number=1,
            ),
            dict(
                number=2,
            ),
        ],
    )
    
    print(f"source: {source}")

    PersistAttr.persist_json(key, source, file_path)

    target = PersistAttr.extract_json(key, file_path)
    
    print(f"target: {target}")

    assert source == target
