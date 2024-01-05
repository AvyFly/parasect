Usage Example with Ardupilot
============================

.. _apj_tool: https://ardupilot.org/dev/docs/apjtools-intro.html
.. _Menu Creation: usage_create_menu.html
.. _Setting Paths: usage_set_paths.html
.. _Python regex: https://docs.python.org/3/library/re.html

This *tutorial* presents a use case of *Parasect* supporting the Ardupilot ecosystem.
*Parasect* can be effective in producing a parameter file that configures an Unmanned Vehicle (UA) completely.

This tutorial mainly targets:

* UA manufacturers, wishing to manage the parameter configuration of their fleet.
* Advanced users, looking for more fine-grained control of their parameter set.

Initial Tuning
--------------

Let's imagine that we have built a custom multicopter of our own design and now we wish to configure the parameters of Ardupilot.
To that goal, let's first obtain the default parameter set of the autopilot.
We connect via our favourite GCS, flash the autopilot with the appropriate airframe and then save the default parameter set, i.e. the parameters and their values as they where on the first boot.
It doesn't matter much if this is done before or after the initial sensor calibration. For the purposes of this tutorial, let's say we saved the file after calibration.

Let's create a folder ``parasect_files`` and place those parameters in a file inside that, named ``defaults.params``.
From now on our working folder will be ``parasect_files``.

The file is going to look something like

.. code-block::

    ACRO_BAL_PITCH   1.000000
    ACRO_BAL_ROLL    1.000000
    ACRO_OPTIONS     0
    ACRO_RP_EXPO     0.300000
    ACRO_RP_RATE     360.000000
    ...
    WPNAV_TER_MARGIN 10.000000
    WP_NAVALT_MIN    0.000000
    WP_YAW_BEHAVIOR  2
    WVANE_ENABLE     0
    ZIGZ_AUTO_ENABLE 0

Let's start tuning our UAV.
We know that our UAV carries a 5000mAh battery (``BATT_CAPACITY=5000``) and we have calculated that we need about 1000mAh to land at our own pace (``BATT_LOW_MAH=1000``).

Then we fly a bit and tune the PID loops. We come up with the following changes:

.. code-block::

    LOIT_SPEED=1500
    ATC_ANG_PIT_P=5.0
    ATC_ANG_RLL_P=5.0
    ATC_RATE_R_MAX=60
    ATC_RATE_P_MAX=60

Finally, we choose that we purposely want the default behaviour regarding what
happens mission after a reboot (``MIS_OPTIONS=0``).

Let's save the parameter file anew, naming it ``my_copter_post_tuning.params``.
Parasect can compare the two parameter sets and highlight the differences:

.. code-block::

    > parasect compare defaults.param my_copter_post_tuning.param
    File comparison : defaults.param | my_copter_post_tuning.param
    ================================================================================
    --------------------------------------------------------------------------------
    Component 1-1:
    --------------------------------------------------------------------------------
    ATC_ANG_PIT_P   : 4.5            | 5
    ATC_ANG_RLL_P   : 4.5            | 5
    ATC_RATE_R_MAX  : 0              | 60
    BARO1_GND_PRESS : 94502.5        | 101079.8
    BARO2_GND_PRESS : 94502.5        | 101080.9
    BATT_CAPACITY   : 3300           | 5000
    BATT_LOW_MAH    : 0              | 1000
    LOIT_SPEED      : 1250           | 1500
    STAT_RUNTIME    : 0              | 123
    ================================================================================
    9 parameters differ


The :func:`compare <parasect.compare>` command of *Parasect* lists the differences between two parameter files.
The tuning changes we made are in there, so we can inspect and make sure that they ended up in our saved file.
But so are some that we didn't actively change. ``STAT_RUNTIME`` is a parameter that constantly changes value so we don't care seeing that in the differences list.
Additionally, calibration values such as ``BARO1_GND_PRESS`` and ``BARO2_GND_PRESS`` are also bound to change automatically and we don't want to manually set them.

Our First Meal
--------------

*Parasect* can help us reproduce this parameter set systematically. For that, we set up a *Menu* folder with the following contents:

.. code-block::

    menu
    ├── custom_dishes
    │   ├── battery.yaml
    │   ├── mission.yaml
    │   └── tuning.yaml
    ├── defaults.param
    ├── meals.yaml
    └── staple_dishes
        ├── calibration.yaml
        └── header.yaml

First off, we copied our ``defaults.param`` file in the ``menu``.
The rest of the menu is made up of ``.yaml`` files. Let's see what each file contains. In ``custom_dishes`` we can name our files as we want, grouping parameters as we like.
For example:

.. code-block:: yaml
    :caption: battery.yaml

    common:
        ingredients:
            - [BATT_CAPACITY, 5000, ~]
            - [BATT_LOW_MAH, 1000, Enough juice to RTL]

``battery.yaml`` contains those parameters and their values related to the battery configuration. Each line is a triplet describing a) the parameter name, b) the parameter value and c) an optional reasoning of why this value was selected (reminder: the ``~`` symbol means ``None`` in ``yaml`` syntax).

.. note::
    The ``common`` and ``ingredients`` keys are significant, but for now they will not be explained. You can read more in `Menu Creation`_.

The contents of ``mission.yaml`` and ``tuning.yaml`` is similar:

.. code-block:: yaml
    :caption: mission.yaml

    common:
        ingredients:
            - [MIS_OPTIONS, 0, The default behaviour is what I want]

.. code-block:: yaml
    :caption: tuning.yaml

    common:
        ingredients:
            - [LOIT_SPEED, 1500, I like things a bit fast]
            - [ATC_ANG_PIT_P, 5, It can use a bit more oomph here]
            - [ATC_ANG_RLL_P, 5, It can use a bit more oomph here]
            - [ATC_RATE_R_MAX, 60, "It's a big bird, so let's take it slow"]
            - [ATC_RATE_P_MAX, 60, "It's a big bird, so let's take it slow"]

Let's now take a look at the ``staple_dishes`` folder.
Its contents can only be specific ``yaml`` files.

In the ``header.yaml`` file we can put custom headers that will always be prepended in our files.
In this example, the header adds two comment lines.

.. code-block:: yaml
    :caption: header.yaml

    formats:
        apm:
            common:
                - "# Maintainer: George Zogopoulos"
            variants:
                my_copter_1:
                    common:
                    - "# Parameter set for my_copter_1"

Finally, remember how calibration parameters would appear earlier in the parameter files comparison, making the results harder to read?
``calibration.yaml`` gives us a chance to fix that.
Any parameter placed here will be ignored by :func:`compare <parasect.compare>`.
Additionally, a `regular expression <Python regex_>`_ can be used here to capture more than one parameter name per line.

.. code-block:: yaml
    :caption: calibration.yaml

    common:
        ingredients:
            - [BARO._GND_PRESS, ~, ~]
            - [COMPASS_DIA_., ~, ~]
            - [RC\d+_MAX, ~, ~]
            - [RC\d+_MIN, ~, ~]
            - [RC\d+_TRIM, ~, ~]
            - [STAT_RUNTIME, ~, ~]

Finally, let's define the `meals.yaml` file, that brings everything together:

.. code-block:: yaml
    :caption: meals.yaml

    my_copter_1:
        defaults: defaults.param
        battery: ~
        tuning: ~
        mission: ~
        header: my_copter_1
        remove_calibration: true

In this file we ask *Parasect* to build a parameter file titled ``my_copter_1.param``, using the ``common`` sections of ``battery.yaml``, ``tuning.yaml`` and ``mission.yaml`` and the ``my_copter_1`` section of ``header.yaml``.
Additionally, we ask it to use ``calibration.yaml`` to remove the calibration parameters from the parameter set.
All of these parameter changes will be done on top of ``defaults.param``. The path we passed to the ``defaults`` keyword is relative to the ``menu`` folder.

Let's now use the :func:`compare <parasect.build>` command to build the file.

.. code-block::

    > parasect build -i menu -f apm -o my_parameters

The command points to the ``menu`` folder for build information.
The output format is of ``apm`` type and the file will be placed in a folder named ``my_parameters``.

Let's see the contents of ``my_parameters/my_copter_1.param``.

.. code-block::

    # Maintainer: George Zogopoulos
    # Parameter set for my_copter_1
    ACRO_BAL_PITCH	1
    ACRO_BAL_ROLL	1
    ACRO_OPTIONS	0
    ...
    WPNAV_TER_MARGIN	10
    WP_NAVALT_MIN	0
    WP_YAW_BEHAVIOR	2
    WVANE_ENABLE	0
    ZIGZ_AUTO_ENABLE	0

Let's compare the produced file with the intended result.

.. code-block::

    ❯ parasect compare my_parameters/my_copter_1.param my_copter_post_tuning.param
    File comparison : my_copter_1.param | my_copter_post_tuning.param
    ================================================================================
    --------------------------------------------------------------------------------
    Component 1-1:
    --------------------------------------------------------------------------------
    BARO1_GND_PRESS : X                 < 101079.8
    BARO2_GND_PRESS : X                 < 101080.9
    BARO3_GND_PRESS : X                 < 0
    COMPASS_DIA_X   : X                 < 1
    COMPASS_DIA_Y   : X                 < 1
    COMPASS_DIA_Z   : X                 < 1
    RC10_MAX        : X                 < 1900
    RC10_MIN        : X                 < 1100
    ...
    RC9_MIN         : X                 < 1100
    RC9_TRIM        : X                 < 1500
    STAT_RUNTIME    : X                 < 123
    ================================================================================
    55 parameters differ

55 Parameters are different! But all of them are calibration parameters, that don't exist in ``my_copter_1.param``, as we asked.
Still, they clutter the comparison. Let's use the ``-s`` option to ignore them.

.. note::

    We still need to point to the ``menu`` folder to let *Parasect* know where ``calibration.yaml`` is, but that can be circumvented by permanently setting the *Parasect* path, as described in `Setting Paths`_.

.. code-block::

    ❯ parasect compare -i menu -s my_parameters/my_copter_1.param my_copter_post_tuning.param
    File comparison : my_copter_1.param | my_copter_post_tuning.param
    ================================================================================
    ================================================================================
    0 parameters differ

Great! The produced parameter file is exactly as we wanted it!
We can write it in our UAV as many times as we want to reset the parameters to their intended values, without fear of overwriting the calibration!

Another UAV Variant
-------------------

We now decide to build another, slightly different airframe, named ``my_copter_2``.
This one will be identical to the previous one, but it will carry a smaller battery.
We adapt ``battery.yaml`` and ``header.yaml`` accordingly.

Since ``my_copter_2`` has a different ``BATT_CAPACITY`` than ``my_copter_1`` but the same ``BATT_LOW_MAH``, we split the battery definition into a ``common`` part and individual ``variants``.

.. code-block:: yaml
    :caption: battery.yaml

    common:
        ingredients:
            - [BATT_LOW_MAH, 1000, Enough juice to RTL]

    variants:
        my_copter_1:
            common:
                ingredients:
                    - [BATT_CAPACITY, 5000, ~]
        my_copter_2:
            common:
                ingredients:
                    - [BATT_CAPACITY, 3000, ~]

While we are at it, we also want to define some parameters as *operator* parameters.
They will be treated the same as *calibration* parameters, by being removed from the parameter file and we can ignore them in comparisons.
This will allow our friend to change them at any time as he pleases to suit his operation better.

To that goat, we add an ``operator.yaml`` file.

.. code-block:: yaml
    :caption: operator.yaml

    common:
        ingredients:
            - [RTL_ALT, ~, ~]
            - [RTL_CONE_SLOPE, ~, ~]
            - [RTL_LOIT_TIME, ~, ~]
            - [FLTMODE., ~, ~]

Finally, we edit the ``meals.yaml`` file to strip the *operator* parameters too.

.. code-block:: yaml
    :caption: meals.yaml

    my_copter_1:
        defaults: defaults.param
        battery: my_copter_1
        tuning: ~
        mission: ~
        header: my_copter_1
        remove_calibration: true
        remove_operator: true

    my_copter_2:
        defaults: defaults.param
        battery: my_copter_2
        tuning: ~
        mission: ~
        header: my_copter_2
        remove_calibration: true
        remove_operator: true

Let's build the files anew and compare them.

.. code-block::

    > parasect build -i menu -f apm -o my_parameters
    > parasect compare my_parameters/my_copter_1.param my_parameters/my_copter_2.param
    File comparison : my_copter_1.param | my_copter_2.param
    ================================================================================
    --------------------------------------------------------------------------------
    Component 1-1:
    --------------------------------------------------------------------------------
    BATT_CAPACITY : 5000              | 3000
    ================================================================================
    1 parameters differ

Excellent! That's just what we wanted!

Let's give this new airframe to a friend! He needs a platform to brush up his flying skills.

Read-Only Parameters
--------------------

Oh no! Our friend came back saying that his drone crashed! He says that suddenly, as the battery got low it fell out of the sky.
First things first, let's compare the ideal parameter file from the actual one, as our friend gave it to us (called ``friend_dump.param``).

.. code-block::

    > parasect compare -i menu -s my_parameters/my_copter_2.param friend_dump.param
    File comparison : my_copter_2.param | friend_dump.param
    ================================================================================
    --------------------------------------------------------------------------------
    Component 1-1:
    --------------------------------------------------------------------------------
    BATT_FS_CRT_ACT : 0                 | 5
    ================================================================================
    1 parameters differ

Oh dear... he had set the critical battery failsafe action to *Terminate*, inadvertently causing the crash.
We will repair his UAV, but let's make sure that doesn't happen again, by making the ``BATT_FS_CRT_ACT`` parameter *read-only*
and use the `appropriate workflow involving the apj-tool <apj_tool_>`_ to bake in its default read-only value.

We add it in the ``mission.yaml`` file and mark it accordingly.

.. code-block:: yaml
    :caption: mission.yaml

    common:
        ingredients:
            - [MIS_OPTIONS, 0, The default behaviour is what I want]
            - [BATT_FS_CRT_ACT, 4, Do the best thing possible apart from crashing @READONLY]

*Parasect* can scan the *reasoning* section for the keyword ``@READONLY`` and add it in the parameter file.
But ``.param`` files containing the ``@READONLY`` flag cause errors when they are loaded in normal GCSs, like MAVProxy.
Thus, the ``.param`` file to be used by the ``apj_tool.py`` will be exported as a different format: :class:`apj <parasect.Formats>`.

We can build only that meal with the desired format

.. code:: bash

     > parasect build -i menu -f apj -c my_copter_2 -o my_parameters


and then inspect the resulting file.

.. code-block::
    :caption: my_copter_2.param

    ...
    BATT_CRT_VOLT	0
    BATT_CURR_PIN	12
    BATT_FS_CRT_ACT	4	@READONLY
    BATT_FS_LOW_ACT	0
    BATT_FS_VOLTSRC	0
    ...

That's just what we need.

Now, to bake the *read-only* status in the firmware, we need to use the `apj_tool`_.
Unfortunately, *apj_tool* can fit only 8 kilobytes of parameters in the ``.apj`` file, whilst our file is a lot larger.

.. code-block:: bash

    > du -h my_parameters/my_copter_2.param
    24K	my_parameters/my_copter_2.param

We have to make a concession and strip our parameter file from the default parameters.
The downside is that we can no longer use the same parameter file with our GCS to reset all the parameters to the intended value.
But we can easily circumvent this issue by simply creating a parameter file exclusively for this use, and explicitly setting defaults to ``None``.

.. code-block:: yaml
    :caption: meals.yaml

    ...

    my_copter_2:
        defaults: defaults.param
        battery: my_copter_2
        tuning: ~
        mission: ~
        header: my_copter_2
        remove_calibration: true
        remove_operator: true

    my_copter_2_apj:
        defaults: ~
        battery: my_copter_2
        tuning: ~
        mission: ~
        header: my_copter_2
        remove_calibration: true
        remove_operator: true
        add_new: true

Note how we have added the ``add_new: true`` entry in the new meal.
This is necessary, because *Parasect* by default does not allow creating new parameters in a set, to prevent typographical errors.
However, in this case we indeed want to start on an empty slate, without a default parameter set, so we have to explicitly allow new parameter names.

The resulting parameter set is, as expected:

.. code-block::
    :caption: my_copter_2_apj.param

    # Maintainer: George Zogopoulos
    # Parameter set for my_copter_2
    ATC_ANGLE_BOOST	1
    ATC_ANG_PIT_P	5
    ATC_ANG_RLL_P	5
    ATC_RATE_P_MAX	60
    ATC_RATE_R_MAX	60
    BATT_CAPACITY	3000
    BATT_FS_CRT_ACT	4	@READONLY
    BATT_LOW_MAH	1000
    LOIT_SPEED	1500
    MIS_OPTIONS	0

We can now bake in the parameters in our ``.apj`` file with the `apj_tool`_.
We assume that ``arducopter.apj`` and ``apj_tool.py`` have been copied into ``parasect_files``.

.. code-block:: bash

    > python3 apj_tool.py --set-file my_parameters/my_copter_2_apj.param arducopter.apj
    Loaded apj file of length 1809920
    Found param defaults max_length=8192 length=282
    Setting defaults from my_parameters/my_copter_2_apj.param
    Saved apj of length 1809920

Success!

Conclusion
----------

This tutorial taught you how to use *Parasect* to compare and create your own parameter sets.
Now go forth and don't ever let mixed parameters ruin your day ever again!
