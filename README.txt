A Defective Celeste Classic & PICO-8 Port to Python 3

- Main script is "cpyleste.py"

- Dependencies are listed in "requirements.txt" and can be installed via pip like so:
    python3 -m pip install -r requirements.txt

    Note: If Numba is giving you problems, remove the decorators and
    numba imports from all areas of the source code

- Requires Python 3.8 or newer

Some other notes about the port:
  When dying for the first time, you will experience an abrupt
  lag spike for just a little bit, this is because the death particles
  class is being JIT'd for the first time when that occurs.
  Every time after that, it should be silky smooth.
  (Same goes with the particles from the big chest)

Uses my Hagia "engine" which pretends to be the PICO-8 sort of.
https://github.com/0xSTAR/hagia

I gotta give credit where credit is due:

  - Credits to the original creators of Celeste Classic:
      -- Maddy Thorson    https://twitter.com/MaddyThorson
      -- Noel Berry       https://twitter.com/noelfb

    They are both amazing, go check them out!
    And if you haven't played the full release of Celeste, you should
    totally check that out as well! https://exok.com/games/celeste/

  - Credits to MeepMoop for his contribution to the Celeste Classic community
  by creating a TAS tool. Some of the collision code for this port  of the game
  was borrowed from them. https://github.com/CelesteClassic/Pyleste
