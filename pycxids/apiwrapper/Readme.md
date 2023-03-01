# api-wrapper
The original api-wrapper from here https://github.com/catenax-ng/catenax-at-home/tree/main/api-wrapper
became deprecated and still had a few bugs in it.

This is an alternative implementation, still keeping the original idea in mind, but fixing some bugs in its behavior, e.g. handling '/' cases

It will also support to switch between 2 'backends' for the IDS protocol. 1 is via EDC and 1 is via `pycxids.core`
