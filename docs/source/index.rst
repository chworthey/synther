Synther Reference
=================

Example Usage
-------------

.. code-block:: python

   import synther as s

   # Construct a project
   proj = s.gen_project()

   # Queue some commands
   virtual_buffer = proj.queue_gen_buffer()
   proj.queue_produce_wave(virtual_buffer, 0, 10, 80, 10, 440, 30000, s.WaveType.SINE)
   proj.queue_produce_wave(virtual_buffer, 0, 10, 80, 10, 440, 30000, s.WaveType.SINE)
   proj.queue_produce_wave(virtual_buffer, 0, 10, 80, 10, 440, 30000, s.WaveType.SINE)

   # IMPORTANT: This next step must be done. It is used to determine when commands should 
   # or should not be executed.
   proj.queue_dump_buffer(virtual_buffer, 'output.wav')  # render wave to file

   # Build. This is the step that will execute the commands if and only if the build system deems it should.
   proj.build()

   # Do you need to execute the command queue anyway? Then do this instead:
   # proj.clean() <-- uncomment
   # proj.build() <-- uncomment

   # Or, a more concise way to do the same as the 2 lines above:
   # proj.rebuild() <-- uncomment

Module Configuration
--------------------

.. autofunction:: synther.set_log_level

.. autoclass:: synther.LogLvl
   :members:

Common Types
------------

.. autoclass:: synther.WaveType
   :members:

Build System
------------

.. autofunction:: synther.gen_project

.. autoclass:: synther.SyntherProject
   :members:

Direct Buffer Manipulation
--------------------------

.. note::
   It is highly recommended you use the build system instead.

.. autofunction:: synther.gen_buffer

.. autofunction:: synther.get_buffer_bytes

.. autofunction:: synther.dump_buffer

.. autofunction:: synther.sample_file

.. autofunction:: synther.produce_wave

.. autofunction:: synther.free_buffer



