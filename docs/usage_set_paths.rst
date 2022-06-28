Setting Paths
=============

*Parasect* needs to know where certain files are to function:

#. To ignore *calibration* or *operator* parameters in :func:`compare <parasect.compare>`, it needs to know where the Meals Menu is, to find the corresponding staple Dishes.
#. To :func:`build <parasect.build>` the Meals Menu, it needs to know its folder path.
#. To :func:`build <parasect.build>` a Meals Menu with the PX4 format, it needs to know the filepath of the default parameters .xml file.

In sum, there are two resources that the user might need to specify:

#. The Meals Menu folder path.
#. The filepath of the autopilot default parameters.

Pointing to the Meals Menu folder
---------------------------------

.. program:: parasect build

By priority, pass the Meals Menu path in the :option:`--input_folder` (:option:`-i`)
option of :func:`compare <parasect.compare>` or :func:`build <parasect.build>`.

Alternatively, with lower priority, you can set the environment variable :envvar:`PARASECT_PATH`.

Pointing to the default parameters file
---------------------------------------

By priority, pass the default parameters filepath in the :option:`--default_parameters` (:option:`-d`)
option of :func:`build <parasect.build>`.

Alternatively, with lower priority, you can set the environment variable :envvar:`PARASECT_DEFAULTS`.
