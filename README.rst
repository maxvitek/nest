Nest
====

Nest is a module for issuing commands to and collecting data from the `Nest Learning Thermostat`_.

Don't let your Nest go unhacked!

This project owes its existence to `this excellent php example`_.

Usage:
------

It may be imported directly, thus:

.. code-block:: pycon

    >>>from nest import Next
    >>>nest = Nest('your.name@email.com', 'p455w0rd')
    >>>nest.set_target_temperature(75)
    ...

Contribute:
-----------

#. Add other Nest commands.  Set fans, humidity target, etc.
#. Is there a better way to choose a target device from multiple devices?
#. Commandline interface?

.. _Nest Learning Thermostat: http://www.nest.com
.. _this excellent php example: https://github.com/gboudreau/nest-api