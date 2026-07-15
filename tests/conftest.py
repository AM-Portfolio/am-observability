def pytest_addoption(parser):
    parser.addoption(
        "--update-goldens",
        action="store_true",
        default=False,
        help="Rewrite testdata/goldens from current generator output",
    )
