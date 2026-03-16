Installing
==========

To install *ioptron-for-python* simply use pip, this will handle all dependencies:

.. code-block:: bash

   pip install ioptron-for-python

Optionally but recommended, install it inside an environment, e.g. for Linux users:

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate

Then, run `pip`.

Usage Example
=============

Here is a simple code to get device model number and set the date and time:

.. code-block:: python

    #port = "/dev/ttyUSB0"  # Linux like
    #port = "COM2"          # Windows like

    mount = Ioptron(port=port)
    mount.init_serial(timedate=True)  # initialize serial and set time-date
    print(mount.mount_model, mount.exec.read.mount_model)
    mount.close_serial()

There are 3 options to retrieve a command:

* Without `exec`: This will get the command string itself. No executed action will be sent to the mount.
    * Example: `mount.move_north`.
* With `exec`: This command will *fast*-execute the command. This means no output will be read.
    * Example: `mount.exec.move_north`.
* With `exec.read`: This command will execute and will retrieve the output the mount sends through the RS-232 connection.
    * Example: `mount.exec.read.move_north`.

Commands with arguments use the same logics. Just add the arguments as parameters:

.. code-block:: python

    mount.exec.moving_rate(9)

For a working example see `Driver_Example <https://github.com/MatheusJCastro/ioptron-for-python/blob/main/examples/Driver_Example.ipynb>`_.