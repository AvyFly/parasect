Menu Creation
=============

To fully utilize the capabilities of *Parasect*, you will need to specify certain information about your desired
autopilot configuration. This comes down to creating a folder structure that represents your *Meals Menu*.

.. _Concepts: concepts.html
.. _Setting Paths: usage_set_paths.html
.. _MAVLink: https://mavlink.io/en/
.. _example px4 test: https://github.com/AvyFly/parasect/tree/master/tests/assets/px4/menu
.. _example generic test: https://github.com/AvyFly/parasect/tree/master/tests/assets/generic/menu

.. note:: It is highly recommended that you read the `Concepts`_ section first and get acquainted with the
   *Restaurant Analogy* that is used as nomenclature.

.. seealso:: You can find a `generic example Meals Menu <example generic test_>`_ as well as an
   `PX4 example Meals Menu <example px4 test_>`_, that are part of the unit tests of *Parasect*.
   Refer to it while following this guide or use them as a starting point for your own use cases.

First, create your main *Parasect* input folder, which we'll call ``menu`` for now (the actual folder name isn't important).
You can place this folder anywhere in your system.
You will point *Parasect* to it later.

By the end of this guide, its tree will look something like this:

.. literalinclude:: assets/generic_menu.txt

Make two subfolders in it: ``custom_dishes`` and ``staple_dishes``.

Filling in Staple Dishes
------------------------

Each file contains all necessary information to create a *Dish*. A Dish is supposed to reflect one coherent set of parameters, for example related to PID gains, peripherals configuration,
Remote Controller configuration or the installed battery.

There are currently four Staple Dishes in *Parasect*: ``calibration.yaml``, ``operator.yaml``, ``header.yaml`` and
``footer.yaml``. They are reserved dishes that are used by *Parasect* in either the comparison or build functions.

``calibration.yaml``: This is a Dish that contains the names of the calibration parameters
of your autopilot. List those parameters here to: a) not take them into account when comparing parameter sets and b)
to remove them from generated parameter sets.
An example Calibration Dish follows:

.. literalinclude:: ../tests/assets/generic/menu/staple_dishes/calibration.yaml
   :language: yaml

Notice how each list item is a triplet of items, representing a parameter.
The first value is the parameter name. The second is the parameter value. For the calibration Dish you do not need to specify a value, you can leave it as None (``~``).
Finally, the third item is a string, where you can document why you chose to include this parameter here. You can also set it to None (as ``~``).

``operator.yaml``: This is a Dish (with the usual Dish syntax) that contains the names of the operator parameters
of your autopilot. List those parameters here to: a) not take them into account when comparing parameter sets and b)
to remove them from generated parameter sets. You do not need to specify a value for a operator parameter either, leave it
as None (``~``).

Its syntax is the same as ``calibration.yaml``.

.. note::

   ``calibration.yaml`` and ``operator.yaml`` are the only Dish files that are used by the ``compare`` command.
   If you only plan to use that and not ``build`` any parameter sets, then you can ignore the rest of this guide.

``header.yaml`` and ``footer.yaml``. These are files that don't follow the usual Dish syntax. They contain the boilerplate
text that your autopilot may require of the generated parameter files.
The top-level dictionary does contain a Common section, that applies to all exported formats, but then alongside is a
``formats`` section.

This reflects the available export :class:`~parasect._helpers.Formats` that *Parasect* offers (e.g. `px4` parameters
and `px4afv1` and `px4afv2` for PX4 airframe files.)

Each named format then contains a ``common`` and ``variants`` section as usual, which you can refer to in your Meal.

An example ``header.yaml`` is:

.. literalinclude:: ../tests/assets/generic/menu/staple_dishes/header.yaml
   :language: yaml


Creating Custom Dishes
----------------------

Next, you can create the Dishes that describe your parameter sets.
Within the ``custom_dishes`` folder, create as many Dish ``.yaml`` files as you want and name them as you like.

In each Dish file, start by defining your Common Ingredients as a list of triplets, just as in ``calibration.yaml`` and ``operator.yaml``.
Each triplet refers to a single parameter and its contents are:

#. The parameter name.
#. The parameter value.
#. A justification string, to remind you why you chose to fix this parameter and why selected this particular value. Can be set to None (``~``).

If you plan to generate only one Meal (a single parameter set), then put all your parameter definitions here.
Otherwise, put in the Common Ingredients **only** those parameters who are common across all of your Meals.

Then, define your Allergen Ingredients. These are parameters that you don't want to exist in your generated parameter set.
They will be removed from the default parameters list, if you point to one as a basis of your Meal.
Some autopilot software group their parameters in *parameter groups* (e.g. PX4). This makes it easier to mark them as allergens as
a whole, by placing the group name in the Allergen Groups section of the Dish.

If you plan to use slightly different versions of your Dish across the different Meals, then add a Variants section in your Dish.
This is a dictionary where you can specialize your Dish with different Ingredients and Allergens for each Variant.

The contents of an example dish are:

.. literalinclude:: ../tests/assets/generic/menu/custom_dishes/meat_and_potatoes.yaml
   :language: yaml

Note that it is possible to nest the Variants more than one level deep.

Creating your Menu
------------------

Now that your Dishes and their Variants are specified, you can bring it all together by designating Meals in your Menu.
Create a ``meals.yaml`` file in the top-level directory of your Menu folder. This is a dictionary from strings to dictionaries.

Each section represents a unique autopilot configuration and it starts with an arbitrary name.

Then, in each row you add Dishes to your Meal. The key is the Dish name and the value is the Dish Variant. Set the
value to None (``~``) to use only the Dish Common section. Refer to the nested Variants using a slash (``/``).

Example Meals Menu:

.. literalinclude:: ../tests/assets/generic/menu/meals.yaml
   :language: yaml

.. _meal-reserved-keywords:

There are also some reserved, optional keywords for the Meal dictionary:

* ``defaults``: Specifies a filepath where the default parameters file is found. If it is not absolute, then it is relative
  to your menu folder. This option overrides the *Parsect* default parameters filepath configuration.

* ``sitl``: Marks the Meal for Simulation-In-The-Loop (SITL) purposes. You can select to build SITL or non-SITL Meals
  with the corresponding argument of the :func:`build <parasect.build>` API function.

* ``hitl``: Marks the Meal for Hardware-In-The-Loop (HITL). In some output formats (e.g. PX4), this affects the output filename.

* ``parent``: Adds a reference to another Meal, to be used as a parent for the current Meal. For more information see section `Parent Meals`_.

* ``remove_calibration``: Removes the Calibration Dish Ingredients from this Meal. **Strongly** recommended to be set to ``true``.

* ``remove_operator``: Removes the Operator Dish Ingredients from this Meal. **Strongly** recommended to be set to ``true``.

* ``add_new``: Allows the addition of Ingredients that are **not stated** in the default parameter set (or the parent,
  if one is specified).

* ``frame_id``: This is applicable to PX4 output formats. It sets the ``SYS_AUTOSTART`` parameter.

Parent Meals
------------

Sometimes you want to specify a base Meal (parameter set) and then a bunch more that are basically identical
to that first one, except for very few changes.
One such example is wanting a basic parameter set and then additional vehicles with adjustments to the values of certain
parameters.
Another example is wanting additional Meal variations configuring a camera mount or a secondary radio.

Instead of re-specifying an identical Meal with the additional Dishes, you can specify the base Meal as the
``parent`` of the new Meal and specify **only the additional** Dishes.

The Default Parameter set is not used for the child-Meals. The parameter set of the parent is used instead.
Editing the parent Ingredients is thus always possible, but to add new parameters that don't exist in the parent Meal
you will need to also set ``add_new`` to ``true``.

.. seealso:: Now that you have created your Meals Menu, find out how to point *Parasect* to it in `Setting Paths`_.
