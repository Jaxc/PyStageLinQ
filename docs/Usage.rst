Using PyStageLinQ
*****************

This page is meant as a companion to the API documentation.
Where the API documentation is more straight facts, this will also describe what is going on under the hood.

Regardless of which service or services you indent to subscribe to PyStageLinQ will need announce itself before
a StageLinQ device will acknowledge it and respond to its requests.
The protocol itself uses both broadcasts and TCP for different parts of its communication.
This is all handled by PyStageLinQ under the hood, using asyncio.
This means that the calling application needs to keep in mind that PyStageLinQ will either work in standalone mode where
it never return when started, and will eventually call back when it detects messages.
There is also the option to run PyStageLinQ as part of a larger Python asyncio program.
The program then needs to make sure that PyStageLinQ gets to execute, and not starve the tasks.

There are two main "levels" of StageLinQ:

#. The discovery level
#. The service level

The following chapters goes deeper into these two levels and what considerations needs to be done by the user of
PyStageLinQ.

The Discovery Level
~~~~~~~~~~~~~~~~~~~

All StageLinQ devices needs to send out a discovery frame as a broadcast, and every StageLinQ device shall monitor for
these messages. The Discovery frame itself contains identifying information about the StageLinQ device, but for
PyStageLinQ it more importantly includes information about which IP and port more information about services can be
requested from.

This discovery broadcast needs to be sent out on the same network as the StageLinQ device, by default PyStageLinQ
will send out a frame periodically on every interface available.
If for some reason the user wants to use only a specific interface, the IP of that interface can be specified when
creating the PyStageLinQ object.
It is also possible to use several interfaces, to do so, initiate the PyStageLinQ with a list of IPs.

It is also possible to set which name PyStageLinQ will announce it self as.
As far as I know this does not have any functional difference, but it is helpful when debugging IP traffic.

Lastly the user shall provide a callback function. This callback will be used when PyStageLinQ discovers a new StageLinQ
device. PyStageLinQ will use the information in the discovery frame to request which services the StageLinQ device
provides, and then supply these services, as well as the StageLinQ device IP address and discovery frame data.

The user can then use this data to subscribe to services. More of that later.

Ways to init PyStageLinQ
^^^^^^^^^^^^^^^^^^^^^^^^
The simples way to call PyStageLinQ is to just add a callback function like so


.. code-block:: python3

    PyStageLinQ = PyStageLinQ(my_callback_function)
    PyStageLinQ.start_standalone()

Starting PyStageLinQ like this will send discovery messages (and discover StageLinQ devices) on all available network
interfaces.

If there is a need to only discover StageLinQ devices on a single interface, the "ip" argument can be used.
To use this put in the IP of the interface you want to use.


.. code-block:: python3

    PyStageLinQ = PyStageLinQ(my_callback_function, ip=169.254.13.37)
    PyStageLinQ.start_standalone()

There is also the possibility to use several interfaces by inputting a list of IPs.

.. code-block:: python3

    PyStageLinQ = PyStageLinQ(my_callback_function, ip=[169.254.13.37, 192.268.1.4])
    PyStageLinQ.start_standalone()

Finally there is the option to name what PyStageLinQ will call it self in discovery frames.
This can be done via the "name" argument

.. code-block:: python3

    PyStageLinQ = PyStageLinQ(my_callback_function, name="My own StageLinQ")
    PyStageLinQ.start_standalone()

The discovery callback
^^^^^^^^^^^^^^^^^^^^^^
The discovery callback is called once PyStageLinQ finds a discovery frame from a new device.
Subsequent frames from the same StageLinQ device will not be causing a new callback.

The callback has three arguments:

* ip - A string with IP to the device.
* Remote StageLinQ device discovery data - This is an StageLinQDiscovery class object. It has information about the
  StageLinQ device that has been detected.
* Services provided list - This is a list of EngineServices.ServiceHandle class objects. It contains information about
  the services available at the remote StageLinQ device.

These can then be used to call the subscribe functions. These are described below
