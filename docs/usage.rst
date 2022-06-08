Usage
=====

.. _Concepts: concepts.html
.. _Reference: reference.html
.. _MAVLink: https://mavlink.io/en/
.. _Menu Creation: usage_create_menu.html
.. _example generic test: https://github.com/AvyFly/parasect/tree/master/tests/assets/generic/menu

.. toctree::
   :hidden:
   :maxdepth: 1

   usage_create_menu

.. seealso:: A full reference of the CLI and the API is available `here <Reference_>`_.

CLI Usage
---------

The primary way of using *Parasect* is as a command-line tool.
It provides two functions, :func:`compare <parasect.compare>` and :func:`build <parasect.build>`.

It is strongly recommended that you first read the `Concepts`_ that *Parasect* employs, if you plan to make full use of it.

Compare
^^^^^^^

At its most basic, a comparison between two parameter files can be invoked by:

.. code:: console

   parasect compare <FILE_1> <FILE_2>

A comparison table will be printed.
Following the MAVLink_ conventions, all parameters are assumed to fall under a Vehicle ID and a Component ID.

Example:

   .. code:: console

      ❯ parasect compare 6fcfa754-186b-41ae-90a4-8de386f712c3.params 607f3c36-a9f8-428e-bc16-2c2615b84291.params
      File comparison  : 6fcfa754-186b-41ae-90a4-8de386f712c3.params | 607f3c36-a9f8-428e-bc16-2c2615b84291.params
      ================================================================================
      --------------------------------------------------------------------------------
      Component 1-1:
      --------------------------------------------------------------------------------
      ASPD_SCALE       : X                                           < 1
      BAT1_A_PER_V     : 36.4                                        | 34
      BAT1_CAPACITY    : 4000                                        | 10000
      BAT1_V_DIV       : 18.2                                        | 19.7
      BAT1_V_EMPTY     : 3.5                                         | 3.55
      [...]


* Parameters whose values are different in each file are printed in one line each.
* Parameters that don't exist in one of the two files will be marked with an `X`
* Parameters that have the same value in both files are not shown.


Typically it is not desirable to show the differences in calibration or operation-specific parameters.
``compare`` offers additional flags to filter out such parameters.

First `create your Meals Menu <Menu Creation_>`_, filling in at least your *calibration* and *operator* *Dishes*.
Then, you can filter out the calibration parameters by

.. code:: console

   parasect compare -s <FILE_1> <FILE_2>

or filter out the operator parameters by

.. code:: console

   parasect compare -u <FILE_1> <FILE_2>

The two flags can be combined.

Build
^^^^^

*Parasect* can generate parameter sets for your autopilot or fleet of autopilots.

First `create your Meals Menu <Menu Creation_>`_. Then, you can generate the parameter sets for all your vehicles with

.. code:: console

   parasect build -o <output_folder> -f <output_format> -i <meals_menu_folder> -d <path_to_default_parameters_file>

Partial output of `our example Meal Menu <example generic test_>`_, on .csv format:

.. literalinclude:: assets/generic_menu_csv/full_meal.csv
   :language: csv

API Usage
---------

*Parasect* also exposes an API for the :func:`compare <parasect.compare>` and :func:`build <parasect.build>` commands, that can be useful in project automation.
Their arguments are identical to their CLI counterparts.

See the :ref:`api_reference` for the full documentation.
