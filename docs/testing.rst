Testing
=======

Make sure you have followed the instructions in `docs/dev_install.rst` and set up the local working copy.
The tests are present in the `tests` module in the root directory.
Specific test files or directories or single test can be selected by specifying the test file names directly on the command line:

#. To run all the tests:
		pytest

#. To test a specific directory run:
		pytest directory_name
		
#. To run tests of a file:
		pytest test_filename.py

#. To run a single test function:
		pytest test_filename.py::single_test
