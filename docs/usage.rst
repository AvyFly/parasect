Usage
=====

.. _Concepts: concepts.html
.. _MAVLink: https://mavlink.io/en/

CLI Usage
---------

The primary way of using *Parasect* is as a command-line tool.
It provides two functions, ``compare`` and ``build``.

It is strongly recommended that you first read the `Concepts`_ that *Parasect* employs, if you plan to make full use of it.

Compare
^^^^^^^

At its most basic, a comparison between two parameter files can be invoked by:

.. code:: console

   parasect compare <FILE_1> <FILE_2>

A comparison table will be printed.
Following the MAVLink_ conventions, all parameters are assumed to fall under a Vehicle ID and a Component ID.

Typically it is not desirable to show the differences in calibration or operation-specific parameters.
``compare`` offers additional flags to filter out such parameters.

First `create your Meals Menu <Menu Creation_>`_, filling in at least your *calibration* and *operator* *dishes*.
Then, you can filter out the calibration parameters by

.. code:: console

   parasect compare -s <FILE_1> <FILE_2>

or filter out the operator parameters by

.. code:: console

   parasect compare -u <FILE_1> <FILE_2>

The two flags can be combined.

Build
^^^^^


Menu Creation
-------------


Full CLI Reference
------------------

.. click:: parasect.__main__:cli
   :prog: parasect
   :nested: full
