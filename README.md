# CIS350_FTPserver
Final project for CIS350 - an encrypted FTP program

## Dependencies (version used for development):
All of these can be installed with `pip install <name>`

To run the project, you will need:
* `rncryptor` (3.2.0)

Additionally, to run tests, the following must be installed:
* `pylint` (1.8.3)
* `pytest` (3.5.0)
* `coverage` (4.5.1)
* `pytest-cov` (2.5.1)

Furthermore, we used the following for development-specific tasks (e.g. documentation generation):
* `Sphinx` (1.7.1)

## Testing / Coverage
To run linting (static analysis + code standard checking), run `pylint ft\_conn file\_info GUI encryption`  
You can also lint our tests by running `pylint tests`  

To run our test cases without coverage measurement, run `pytest`  
To run our test cases _with_ coverage measurement, run `pytest --cov=.`

## Documentation
To generate html documentation pages, run `make html` from within the `doc` subdirectory. After it terminates, the root documentation will be at `doc/build/html/index.html`
