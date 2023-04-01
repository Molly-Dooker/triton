import torch

import triton
import triton.language as tl

src = """
--[----->+<]>--.+.+.[--->+<]>--.+[----->+<]>.------------.--[--->+<]>-.-------.++++++++.---------.-------------.++++++++
++++.------.+++++++++++++.----.---------.+++++++.[--->+<]>++++.[---->+<]>.[->+++<]>++....+++.---.[-->+++++<]>.[--->+<]>-
.------.+++++.++++++.+++[->+++<]>.+++++++++++++.+.+[---->+<]>+++.---[->++++<]>.-----.[--->+<]>-----.+[----->+<]>.-------
-----.--[--->+<]>-.--.---------.------.++.[--->+<]>----.>++++++++++.[->+++<]>++....[->+++<]>+.--.---[->++++<]>.++++.--.[
++>---<]>+.------------.[->+++<]>++.---.---[->++++<]>.++++.--.[++>---<]>+.------------.+[->+++<]>.----.---[->++++<]>.+++
+.--.[++>---<]>+.>++++++++++.[->+++<]>++....+++.---.++++++[->++<]>+.-[------>+<]>-.--[--->+<]>-.--.---------.-[--->+<]>.
[---->+<]>++.+[->+++<]>+.+++++.++++.--------.+++++++++.+++++.----------.++++++.-.+++++.>++++++++++.[->+++<]>++....++++++
[->++<]>+.--[->++++<]>.------------.[-->+++++<]>--.[-->+<]>+++++.------------.--[-->+++++<]>.[->++++<]>.>++++++++++.[->+
++<]>++....+++.---.>-[--->+<]>-.[---->+++++<]>-.---.--[--->+<]>-.---[->++++<]>-.+.--.---------.-----.+.--[--->+<]>-.--[-
>++++<]>--.[->+++<]>-.--[--->+<]>---.---------.--------.+.++++++++++.-------.[--->+<]>----.+[---->+<]>+++.---[----->++<]
>.-------------.+++++++++++.++.-------------.[--->+<]>----.++++[->+++<]>.+++++++++.++++++.[---->+<]>+++.-[--->++<]>--.++
+++++.++++++++.+[---->+<]>++.+[----->+<]>.++++++++.+[->+++<]>+.+++++.--[--->+<]>--.---[->++++<]>.-----.[--->+<]>-----.-[
--->++<]>-.+++++.-----------.-[--->+<]>----.-------------.----.--[--->+<]>--.++++[->+++<]>.--[--->+<]>-.---[->++++<]>.--
----------.---.--[--->+<]>-.[-->+++++++<]>.++++.--.[-->+++++<]>+++.[->+++<]>++.[--->+<]>+++.-[---->+<]>++.--[->++++<]>-.
+[->+++<]>.---.+++++++++.-[->+++++<]>-.+[----->+<]>.++.+++++++.[------>+<]>.+++++.-------.-[--->+<]>--.[->+++<]>++.[--->
+<]>+++.-[---->+<]>++.[-->+++<]>+.>++++++++++.[->+++<]>++....+++.---.+[->+++<]>++.+++++++.-------.++++++++.--------.++++
+++++.++++++.[---->+<]>+++.-[--->++<]>-.+++++.-[->+++++<]>-.[->+++<]>+.-[->+++<]>.[-->+++++++<]>.[----->++<]>+.--[--->+<
]>---.++.-----------.------.-[--->+<]>-.---------.-----------.--[--->+<]>---.[-->+++++<]>+++.+[->+++<]>+.+++++.++++.----
----.+++++++++.+++++.----------.++++++.-.[----->++<]>++.++[--->++<]>.++[->++<]>+.[--->++<]>.+[--->+<]>++.--[->+++<]>-.++
[--->++<]>.---[->++++<]>-.+.--.---------.-----.+.------.++.++++++++++++.[->+++++<]>-.-[--->++<]>-.++++++++++.+[---->+<]>
+++.-[--->++<]>--.+++++++.++++++++.+[---->+<]>++.+[----->+<]>.++++++++.+[->+++<]>+.+++++.--[--->+<]>--.---[->++++<]>.---
--.[--->+<]>-----.-[--->++<]>-.+++++.-----------.-[--->+<]>----.-------------.----.--[--->+<]>--.++++[->+++<]>.--[--->+<
]>-.[->+++<]>+.--.---[->++++<]>.++++.--.>++++++++++.[->+++<]>++....+++.---.[->+++<]>++.[--->+<]>+++.-[---->+<]>++.---[->
++++<]>.-----.[--->+<]>-----.++[->+++<]>+.--.[--->+<]>---.[---->+<]>+++.---[->++++<]>.------------.---.--[--->+<]>-.+[->
+++<]>++.+++++++.-------.++++++++.--------.+++++++++.++++++.[---->+<]>+++.+++++[->+++<]>.-.---------.--[--->+<]>-.---[--
--->++<]>.---.++++++++.+[---->+<]>++.+[->+++<]>+.+++++++++++.++++++++.---------.-[->+++++<]>-.++++++++.-[--->+++++<]>.-[
-->+<]>.-[--->++<]>--.-------.--[--->+<]>--.+[---->+<]>+++.++++++[->++<]>+.-----[->++++<]>.---[----->++<]>.---.++++++++.
----.-[--->+<]>+++.>++++++++++.[->+++<]>++....---[->++++<]>-.+.--.---------.-----.+.------.++.++++++++++++.+[----->++<]>
.------------.---[->++++<]>-.+.--.---------.-----.+.------.++.++++++++++.+++[----->++<]>.>++++++++++.[->+++<]>++....---[
->++++<]>-.+.--.---------.-----.+.------.+++.+++++++++.+++[----->++<]>.------------.---[->++++<]>-.+.--.---------.-----.
+.------.+++.++++++++++++.[----->++<]>.>++++++++++.[->+++<]>++....---[->++++<]>-.+.--.---------.-----.+.------.++++.++++
++++++.+[----->++<]>.------------.---[->++++<]>-.+.--.---------.-----.+.------.++++.+++++++++++.[----->++<]>.>++++++++++
.[->+++<]>++....+++.---.++++++[->++<]>+.>--[----->+<]>-.[--->+<]>---.+[->+++<]>++.-[-->+<]>---.--[----->+<]>+.[----->++<
]>+.--[--->+<]>---.+++[->+++<]>++.++++++++++++.--------.[--->+<]>---.+++[->+++<]>.+++++++++++++.+.>++++++++++.[->+++<]>+
+....+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.
+[->+++++<]>+.[----->++++<]>+.+[->++++<]>++.[-->+<]>+++.---[->++++<]>.--------.[-->+<]>--------.--[--->+<]>-.+++++++++++
+.-.+++++.+.+++[->+++<]>.[--->+<]>+.--------.++.[++>---<]>+.------------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.-
-[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--------->++<]>.[->++++<]>++.[-->+<]>
+++.---[->++++<]>.--------.[-->+<]>--------.--[--->+<]>-.++++++++++++.-.+++++.+.+++[->+++<]>.[--->+<]>+.--------.++.[++>
---<]>+.------------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<
]>.-[----->+<]>.+[->+++++<]>+.[--->+++++<]>++.[------->++<]>.[-->+<]>+++.---[->++++<]>.--------.[-->+<]>--------.--[--->
+<]>-.++++++++++++.-.+++++.+.+++[->+++<]>.[--->+<]>+.--------.++.[++>---<]>+.>++++++++++.[->+++<]>++....+++[->++<]>+.+++
++++++++.---.++++++.-----.+++++++++++++++.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++
<]>+.+[->++++<]>++.[-->+<]>+++.---[->++++<]>.--------.[-->+<]>--------.--[--->+<]>-.++++++++++++.-.+++++.+.+++[->+++<]>.
[--->+<]>+.--------.++.[++>---<]>+.>++++++++++.[->+++<]>++....[->++<]>+.++.>-[--->+<]>-.-----------.>+[--->++<]>.++[----
>+++<]>-.>-[--->+<]>-.-----------.++++++.-.[->++++<]>++.[-->+<]>+++.---[->++++<]>.--------.[-->+<]>--------.--[--->+<]>-
.++++++++++++.-.+++++.+.+++[->+++<]>.[--->+<]>+.--------.++.[++>---<]>+.>++++++++++.[->++++<]>+.-[-->+++<]>--.>+++++++++
+.[->+++<]>++....++...+++[->++<]>+.[--->++++<]>+.+++++++++++++.----.---------.+++++++.[++>---<]>--.++[->+++<]>.+++++++++
.+++.[-->+++++<]>+++.+[->+++<]>.++++++++++++.--.+++.+++++.-.-----------.+++++.-------.-[--->+<]>--.---[->++++<]>.-------
-----.---.--[--->+<]>-.+[----->+<]>.------------.--[--->+<]>-.-------.++++++++.---------.[++>---<]>--.+[->++<]>+.-[-->+<
]>-.-[->++<]>-.+[-->+<]>+.[->++<]>+.-[-->+<]>.--[->++++<]>.[---->+<]>++.+[->++<]>.[--->++<]>++.>++++++++++.[->+++<]>++..
..[->++<]>+.-[-->+<]>.-[--->++<]>--.-------.--[--->+<]>--.+[---->+<]>+++.---[->++++<]>-.-----------.-------.-[++>-----<]
>.-----------.--[--->+<]>-.++++++++.-[->++<]>-.--[->++++<]>.------------.--[-->+++++<]>.-[->++++<]>+.+++.------------.+[
->++<]>.[-->+<]>-.-[--->++<]>--.-------.--[--->+<]>--.+[---->+<]>+++.---[->++++<]>-.-----------.-------.-[++>-----<]>.--
---------.--[--->+<]>-.++++++++.--[->++<]>-.[->++++<]>.------------.[-->+++++<]>--.[-->+<]>++.---------.[->+++<]>+.+++++
++++++++.----------.-[--->+<]>-.+[->++<]>+.-[-->+<]>-.-[--->++<]>--.-------.--[--->+<]>--.+[---->+<]>+++.---[->++++<]>-.
-----------.-------.-[++>-----<]>.-----------.--[--->+<]>-.++++++++.-[->++<]>-.--[->++++<]>.------------.[-->+++++<]>--.
[-->+<]>++.>++++++++++.[->+++<]>++....++...>++++++++++.[->+++<]>++....+++.---.--[-->+++<]>..............................
.............................>++++++++++.[->+++<]>++....+++.---.++++++[->++<]>+.-[------>+<]>-.-[++>-----<]>.[------->++
<]>.[-->+++++++<]>.++.---.--------.+++++++++++.+++[->+++<]>++.++++++++++++.[->+++++<]>-.-[--->++<]>-.-----.--[--->+<]>--
-.+[---->+<]>+++.[->+++<]>.[++>-----<]>.-------.-----.----.[->+++<]>.---[->++++<]>.-----.[--->+<]>-----.---[->++++<]>.--
----------.---.--[--->+<]>-.[->+++<]>++.++++++++++.+++.------------.++++++++.-[++>---<]>+.+++++[->+++<]>.---------.[--->
+<]>--.+[->++<]>+.-[-->+<]>-.-[--->++<]>-.+++++++++++.[---->+<]>+++.---[->++++<]>-.-----------.+++++++.++++++.---------.
--------.-[--->+<]>-.+[->+++<]>.++++++++++++.--.+++.+++++.-.+++[->+++<]>.[->+++<]>-.>++++++++++.[->+++<]>++....+++.---.>
-[--->+<]>-.[---->+++++<]>-.+.++++++++++.+[---->+<]>+++.-[--->++<]>-.++++++++++.+[---->+<]>+++.+[->+++<]>+.+++++++++++.-
.---------.--[--->+<]>-.-[--->++<]>-.+++++.-[->+++++<]>-.[->+++<]>+.-[->+++<]>.++[->+++<]>+.+++++++++++.---.++++++.-----
.-----------.-.-[--->+<]>-.+++++[->+++<]>.+++.--------------.+.+++++++++++++.---------.+++++.-------.-[--->+<]>--.---[->
++++<]>.-----.[--->+<]>-----.[-->+++++++<]>.++.---.--.++.+++++.+++[->+++<]>.--[--->+<]>-.++++++[->++<]>.-[--->++<]>.--[-
-->++<]>.+[->+++<]>+.---.--[--->+<]>-.+[->+++<]>++.-[->+++<]>.---[----->++<]>.-------------.[--->+<]>--.--.++++[->+++<]>
.>++++++++++.[->+++<]>++....+++.---.>-[--->+<]>--.[----->+++<]>..--[--->+<]>-.[->+++<]>+.+.+++++++++++++.+++++++.+[->+++
<]>.--[--->+<]>-.[->+++<]>.++[->++++++<]>.-[--->++<]>.--[--->++<]>.+[->++<]>+.-[-->+++<]>--.++.+++++.---.--[--->+<]>-.[-
->+++++<]>-.+[--->+<]>.++++.-----------.++++.----.-[--->+<]>++.[->+++++<]>-.--[--->+<]>-.-----------.++++++.-.+++++.++[-
>+++<]>+.[->+++<]>.---[->++++<]>-.++++[->+++<]>.--.-[--->+<]>--.-----------.++++++.-.-[->+++++<]>-.++[->+++<]>.+++++++++
.+++.[-->+++++<]>+++.+[->+++<]>+.+.[--->+<]>---.+[->+++<]>++.++++++++.+++.+++++++.>++++++++++.[->+++<]>++....[-->+++++++
<]>.-------.-----.-[--->+<]>-.-[->++<]>-.+[-->+<]>+.---[->++++<]>.--------.[-->+<]>--------.++[----->+<]>.++.---.-------
-.+++++++++++.+++[->+++<]>++.++++++++++++.--------------.++++++++++.-----.-[->+++<]>-.--[--->+<]>-.+[--->+<]>++.[->+++<]
>+.++++++++++.+[-->+<]>+++.[->+++++<]>-.-------.>++++++++++.[->+++<]>++....+[----->+<]>+.+++++++.--------.--------------
.---[->++++<]>.-------.-----.-----.++++++++++++++.[->+++++<]>-.-[->++<]>-.+[-->+<]>+.---[->++++<]>.--------.[-->+<]>----
----.--[--->+<]>-.+.+++++.[->++++++<]>.-[--->+<]>+.-[->++<]>-.--[->++++<]>.------------.+[->++<]>.++++++++++.+++.[----->
+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++<]>+.+[-->+<
]>++.>++++++++++.[->+++<]>++....+[----->+<]>+.+++++++.--------.--------------.---[->++++<]>.-------.-----.-----.++++++++
+++++++.-[->+++++<]>-.-[->++<]>-.+[-->+<]>+.---[->++++<]>.--------.[-->+<]>--------.--[--->+<]>-.+.+++++.[->++++++<]>.-[
--->+<]>+.-[->++<]>.[-->+<]>+++++.------------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.-----------
-.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--------->++<]>.[-->+<]>++.>++++++++++.[->+++<]>++....+[----->+
<]>+.+++++++.--------.--------------.---[->++++<]>.-------.-----.-----.++++++++++++.-[++>---<]>+.-[->++<]>-.+[-->+<]>+.-
--[->++++<]>.--------.[-->+<]>--------.--[--->+<]>-.+.+++++.[->++++++<]>.-[--->+<]>+.--[->++<]>-.[->++++<]>.------------
.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->
+++++<]>+.[--->+++++<]>++.-[->++++<]>+.>++++++++++.[->+++<]>++....+[----->+<]>+.+++++++.--------.--------------.---[->++
++<]>.-------.-----.-----.++++++++++.+++++.---------------.++++++++.+++++++++++.---.++++++.-----.[------->++<]>.-[->++<]
>-.+[-->+<]>+.+++[->++<]>+.+++++++++++.---.++++++.-----.+++++++++++++++.------------.----------.-[---->+++++<]>.-[----->
+<]>.+[->+++++<]>+.[----->++++<]>+.-----[->++++<]>.++++++++++.----------.+[----->+<]>+.+++++++.--------.--------------.-
--[->++++<]>.-------.-----.-----.+++++++++++++++.>++++++++++.[->+++<]>++....++[->+++<]>+.+++++++++++.---.++++++.-----.[-
---->++<]>-.++++++++++.-----.-[--->+<]>-.-[->++<]>-.+[-->+<]>+.[-->+++++++<]>.-------.-----.-[--->+<]>-.[-->+++<]>-..+[-
-->++<]>.+[----->+<]>+.+++++++.--------.--------------.---[->++++<]>.-------.-----.-----.++++++++++.+++++.--------------
-.++++++++.+++++++++++.---.++++++.-----.>++++++++++.[->+++<]>++....++[->+++<]>.+++.+++++++++.+.+.+[->+++<]>.---[->++++<]
>.-------.-----.-----.++++++++++++++.[->+++++<]>-.-[->++<]>-.+[-->+<]>+.++[->+++<]>+.+++++++++++.---.++++++.-----.[-----
>++<]>-.++++++++++.-----.-[--->+<]>-.++++++++++.----------.+++[->++<]>+.+++++++++++.---.++++++.-----.+++++++++++++++.---
---------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++<]>+.>++++++++++.[->+++<]>++....++[->+++<]>+.
+++++++++++.---.++++++.-----.[----->++<]>-.[--->+<]>--.----------.-[--->+<]>++.---[->+++<]>.------.++++++++++++++.[->+++
++<]>-.-[->++<]>-.+[-->+<]>+.+[----->+<]>.----.+++++.++[++>---<]>.[--->++<]>--.+++++++.--------.--------------.---[->+++
+<]>.-------.-----.-----.++++++++++++++.[->+++++<]>-.--[-->+++<]>.[--->++<]>++.++[->+++<]>.+++.+++++++++.+.+.+[->+++<]>.
---[->++++<]>.-------.-----.-----.++++++++++++++.+[----->++<]>.------------.+++[->++<]>+.+++++++++++.---.++++++.-----.++
+++++++++++++.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++<]>+.+[-->+<]>++.>++++++++++
.[->+++<]>++....[-->+++++++<]>.-------.-----.-----.++++++++++++++.[->+++++<]>-.-[->++<]>-.+[-->+<]>+.++[->+++<]>.+++.+++
++++++.+.+.+[->+++<]>.---[->++++<]>.-------.-----.-----.++++++++++++++.[->+++++<]>-.+++++++++++.-----------.++++++++.[--
->++<]>.-------.-----.-[--->+<]>-.+++++.-----.++[->+++<]>+.+++++++++++.---.++++++.-----.[----->++<]>-.[--->+<]>--.------
----.-[--->+<]>++.---[->+++<]>.------.++++++++++++++.+++[++>---<]>+.>++++++++++.[->+++<]>++....[-->+++++++<]>.-------.--
---.-----.+++++++++++++++.-[->+++++<]>-.-[->++<]>-.+[-->+<]>+.++++++++.[--->++<]>.-------.-----.-[--->+<]>-.+++++.-----.
+[----->+<]>+.+++++++.--------.--------------.---[->++++<]>.-------.-----.-----.++++++++++.+++++.---------------.+++++++
+.+++++++++++.---.++++++.-----.[++>---<]>+.---------.[-->+++<]>-..+[--->++<]>.++[->+++<]>+.+++++++++++.---.++++++.-----.
[----->++<]>-.[--->+<]>--.----------.-[--->+<]>++.---[->+++<]>.------.++++++++++++++.>++++++++++..[->+++<]>++....+++.---
.--[-->+++<]>..........................................................>++++++++++.[->+++<]>++....+++.---.+[->++<]>+.+[+
+++>---<]>-.-------------.----.--[--->+<]>-.+++[->+++<]>.--[--->+<]>-.[-->+++++++<]>.-.------.+++++.++++++.+++[->+++<]>.
+++++++++++++.+.+[---->+<]>+++.++[->+++<]>.+++++++++.+++.[-->+++++<]>+++.---[->++++<]>.------------.---.--[--->+<]>-.++[
->+++<]>.+++.+++++++++.+.+.[---->+<]>+++.[->+++<]>++.++++++++++.+++.------------.++++++++.++++++++.+[---->+<]>+++.+++++[
->+++<]>.---------.[--->+<]>--.[->++<]>+.-[-->+<]>.[->+++<]>+.+++++++++++++.----------.-[--->+<]>-.+[->++<]>.[--->++<]>+
+.>++++++++++.[->+++<]>++....+++.---.---[->+++<]>.++[->++++<]>+.--[--->+<]>-.--[->++++<]>-.+[->+++<]>+.+++..[++>---<]>--
.[->+++<]>+.+++.--[--->+<]>.[->+++<]>-.+++++++++++++.-----------.++.--[--->+<]>-.---[->++++<]>.------------.+.++++++++++
.+[---->+<]>+++.[-->+++++++<]>.-.------.+++++.++++++.+++[->+++<]>.+++++++++++++.[-->+++++<]>+++.[->+++<]>+.--[--->+<]>--
.+[---->+<]>+++.--[->++++<]>-.[->+++<]>.--[--->+<]>-.+[----->+<]>.++.+++++++.+[->+++<]>.--[--->+<]>-.-[--->++<]>-.+++++.
-[->+++++<]>-.---[->++++<]>.------------.---.--[--->+<]>-.--[-->+++++<]>.---[->++++<]>.+[->+++<]>+.+++++.+++++++++.-----
--------.--.-[--->+<]>--.-----------.++++++.-.>++++++++++.[->+++<]>++....+++.---.[->+++<]>+.+++++++++++++.----------.-[-
-->+<]>-.[->+++<]>+.++..-[--->+<]>-.--------.++++++++.---------.-----------.--[--->+<]>-.+++[->+++<]>.>++++++++++.[->+++
<]>++....+++.---.[->+++<]>+.--.---[->++++<]>.++++.--.+.+[---->+<]>+++.-[--->++<]>-.++++++++++.+[---->+<]>+++.[->+++<]>+.
-[->+++<]>.[->+++<]>++.++++++++++.+++.------------.++++++++.-[++>---<]>+.+++++[->+++<]>.---------.[--->+<]>--.--[->+++<]
>+.---[---->+++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+
<]>.+[->+++++<]>+.[----->++++<]>+.--[->++++<]>.------------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]
>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--->+++++<]>++.-----[->+++++<]>-.[--->+<]>+.[-->++
+++++<]>.-.------.+++++.++++++.+++[->+++<]>.+++++++++++++.+.>++++++++++.[->+++<]>++....+++.---.[->+++<]>++.---.---[->+++
+<]>.++++.--.+.+[---->+<]>+++.-[--->++<]>-.++++++++++.+[---->+<]>+++.[->+++<]>+.-[->+++<]>.[->+++<]>++.++++++++++.+++.--
----------.++++++++.-[++>---<]>+.+++++[->+++<]>.---------.[--->+<]>--.--[->+++<]>+.---[---->+++<]>.++++++++++.+++.[-----
>+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--->+++++<]>++.[->+++
+<]>.------------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.
-[----->+<]>.+[->+++++<]>+.+++++++++++++++.---[--->+++++<]>.[--->+<]>+.[-->+++++++<]>.-.------.+++++.++++++.+++[->+++<]>
.+++++++++++++.+.>++++++++++.[->+++<]>++....+++.---.---[->++++<]>-.++++[->+++<]>..--[--->+<]>-.[->+++<]>+.+.++++++++++++
+.+++++++.+[->+++<]>.--[--->+<]>-.[->+++<]>.[-->+++++++<]>.[--->+<]>-.------.+++++.++++++.+++[->+++<]>.+++++++++++++.[--
>+++++<]>+++.[->++<]>+.--[----->+<]>-.---------.+++++++++++.------------.+++++.--------.[--->+<]>---.-----------.------.
---.[->+++<]>.---[->++++<]>-.++++[->+++<]>.--.-[--->+<]>--.-----------.++++++.-.-[->+++++<]>-.++[->+++<]>.+++++++++.+++.
[-->+++++<]>+++.+[->+++<]>+.+.[--->+<]>---.+[->+++<]>++.++++++++.+++.+++++++.>++++++++++.[->+++<]>++....+++++[->+++<]>.-
--------..+++++++++++++.++[->+++<]>.++.++++++++++++.[->+++++<]>-.-[->++<]>-.+[-->+<]>+.[-->+++++++<]>.-------.-----.----
-.++++++++++++++.[->+++++<]>-.++++++++++.----------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------
------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++<]>+.-----[->++++<]>.+++++++++++.-----------.---
[->++++<]>.--------.[-->+<]>--------.++[->++<]>+.--[--->+<]>---.+++[->+++<]>++.+++++++++++++.-------.--.--[->+++<]>-.+++
+++++.----.------------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++
++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++<]>+.+[-->+<]>++.>++++++++++.[->+++<]>++....+++++[->+++<]>.---------..++++++
+++++++.++[->+++<]>.+++.++++++++++++.-[->+++++<]>-.-[->++<]>-.+[-->+<]>+.[-->+++++++<]>.-------.-----.-----.++++++++++++
+++.-[->+++++<]>-.++++++++++.----------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.-----
-----.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--------->++<]>.++[----->++<]>.+++++++++++.-----------.---[->++++<]>.-
-------.[-->+<]>--------.++[->++<]>+.--[--->+<]>---.+++[->+++<]>++.+++++++++++++.-------.--.--[->+++<]>-.++++++++.----.-
-----------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----
->+<]>.+[->+++++<]>+.[--------->++<]>.[-->+<]>++.>++++++++++.[->+++<]>++....+++++[->+++<]>.---------..+++++++++++++.++[-
>+++<]>.++++++++++++.-[++>---<]>+.-[->++<]>-.+[-->+<]>+.---[->++++<]>.--------.[-->+<]>--------.++[->++<]>+.--[--->+<]>-
--.+++[->+++<]>++.+++++++++++++.-------.--.--[->+++<]>-.++++++++.----.------------.+[->++<]>.++++++++++.+++.[----->+<]>.
++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--->+++++<]>++.-[->++++<]>+
.>++++++++++.[->+++<]>++....[->+++<]>+.--.---[->++++<]>.++++.--.+.+[---->+<]>+++.-[->++<]>-.+[-->+<]>+.[->+++<]>+.--.---
[->++++<]>.++++.--.[-->+++++<]>+++.+++++++++++.-----------.++++++++.[--->++<]>-.---------..+++++++++++++.++[->+++<]>.++.
++++++++++++.>+[--->++<]>+++++.-[--->++<]>--.++[->+++++<]>.------------.[-->+++++<]>--.-[--->+<]>.-.---------.--------.[
--->+<]>+.++++++++++.----------.---[->++++<]>-.+.--.---------.-----.+.------.++.++++++++++++.[->+++++<]>-.+++++++++++.--
---------.+++++[->+++<]>.---------..+++++++++++++.++[->+++<]>.++++++++++++.[--->+++++<]>--.-------------.-[--->+<]>.-.--
-------.-[->+++<]>.------------.---[->++<]>.[->++++++<]>+.[--->+<]>+.++++++++++.----------.---[->++++<]>-.+.--.---------
.-----.+.------.++.++++++++++.--[----->++<]>-.>++++++++++.[->+++<]>++....[->+++<]>++.---.---[->++++<]>.++++.--.+.+[---->
+<]>+++.-[->++<]>-.+[-->+<]>+.[->+++<]>++.---.---[->++++<]>.++++.--.[-->+++++<]>+++.+++++++++++.-----------.++++++++.[--
->++<]>-.---------..+++++++++++++.++[->+++<]>.++++++++++++.[--->+++++<]>--.-[--->++<]>--.++[->+++++<]>.------------.[-->
+++++<]>--.-[--->+<]>.-.---------.--------.[--->+<]>+.++++++++++.----------.---[->++++<]>-.+.--.---------.-----.+.------
.+++.+++++++++.-[++>---<]>+.+++++++++++.-----------.+++++[->+++<]>.---------..+++++++++++++.++[->+++<]>.+++.++++++++++++
.+[------->+<]>++.-------------.-[--->+<]>.-.---------.-[->+++<]>.------------.---[->++<]>.[->++++++<]>+.[--->+<]>+.++++
++++++.----------.---[->++++<]>-.+.--.---------.-----.+.------.+++.++++++++++++.++[++>---<]>+.>++++++++++..[->+++<]>++..
..+++.---.--[-->+++<]>...........................................................>++++++++++.[->+++<]>++....+++.---.++++
[->++<]>+.[----->+<]>-.+++[->+++<]>.+++++++++++++.+++[->+++<]>++.--[--->+<]>-.+++[->+++<]>.--[--->+<]>-.---[->++++<]>.--
---.[--->+<]>-----.+[->+++<]>.++++++++++++.--.+++.+++++.-.+++[->+++<]>.--[--->+<]>-.[->+++<]>+.-[->+++<]>.[->+++<]>++.++
++++++++.+++.------------.++++++++.-[++>---<]>+.+++++[->+++<]>.---------.[--->+<]>--.---[->++++<]>.------------.---.--[-
-->+<]>-.+[->++<]>+.-[-->+<]>-.+[----->+<]>.------------.--[--->+<]>-.--.---------.-[--->+<]>.>++++++++++.[->+++<]>++...
.+++.---.---[->+++<]>.++[->++++<]>+.--[--->+<]>-.[->+++<]>+.++..-[--->+<]>-.--------.++++++++.---------.-----------.--[-
-->+<]>-.+++[->+++<]>.--[--->+<]>-.-[--->++<]>-.+++++.++++++.-----.[--->+<]>-----.[->+++<]>+.-[->+++<]>.[->+++<]>.-----.
---[---->+++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>
.+[->+++++<]>+.[----->++++<]>+.--[->++++<]>.------------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.-
-----------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--------->++<]>.+++++++++++++++.+++.[->+++<]>.[->+++<
]>++.++++++++++.+++.------------.++++++++.>++++++++++.[->+++<]>++....+++.---.+++++[->+++<]>.---------.[--->+<]>--.++[->+
++<]>.++++++++++.>-[----->+<]>.-.--[--->++<]>.--[->++++<]>--.[->+++<]>-.+++++++++++.+++++++++.++[->+++<]>.[--->+<]>----.
+[---->+<]>+++.++[->+++<]>.+++++++++.+++.[-->+++++<]>+++.-[--->++<]>--.+.--.+.---.+++++++++++++.[-->+++++<]>+++.[->+++<]
>+.++..-[--->+<]>-.---.+++[->+++<]>++.++.-[--->+<]>+++.-----[++>---<]>.>++++++++++.[->+++<]>++....+++.---.[->+++<]>.+.++
..-[--->+<]>-.--------.++++++++.---------.-----------.--[--->+<]>-.-----.+++.+++[->+++<]>+.[->+++<]>.--[->++++<]>-.+[->+
++<]>+.+++..[++>---<]>--.[->+++<]>++.+++.--[--->+<]>-.+[->+++<]>.++++++++++++.-.++++++++.+[->+++<]>.+++++++++++++.++.+++
[->+++<]>.-.-[--->+<]>-.[->+++<]>++.-.++.++++++++.-[++>---<]>+.---[->++++<]>.-----.[--->+<]>-----.++[->+++<]>.++++++++++
.[->+++++<]>+.+++++.[-->+<]>+++++.[->+++<]>+.+++++.-[--->+<]>---.+++[->+++<]>.+++++++++++++.[-->+++++<]>+++.---[->++++<]
>.------------.---.--[--->+<]>-.++[--->++<]>.+++..+.>++++++++++.[->+++<]>++....[->+++<]>+.++..-[--->+<]>-.--------.+++++
+++.---------.-----------.--[--->+<]>-.-----.+++.[-->+++++<]>+++.-[->++<]>-.+[-->+<]>+.---[->++++<]>.--------.[-->+<]>--
------.>----[-->+++<]>.---[->+++<]>.+++++++++++++.---.++++.-[--->+<]>++..++++[-->+++<]>.++++++++++.+++.[----->+<]>.+++++
+++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++<]>+.--[->++++<]>.----
--------.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+
<]>.+[->+++++<]>+.[--------->++<]>.[-->+<]>++.+++.------------.+[->+++<]>+.--[--->+<]>--.+++++.---------.-----------.-[+
+++>-----<]>.---[->++<]>.--------.[-->+<]>--------.+[--->+<]>+.++++++.+++.--------------.--[--->+<]>-.>-[----->+<]>.-.--
-------.>++++++++++.[->+++<]>++....++[->+++<]>.+++++++++.+++.[-->+++++<]>+++.-[--->++<]>+.-[++>---<]>+.-[--->++<]>-.++++
+.-[->+++++<]>-.---[----->++<]>.+++[->+++<]>++.+++++++++++++.-------.--.--[->+++<]>-.++++++++.----.------------.+[----->
+<]>+.+++++++.--------.--------------.---[->++++<]>.-------.-----.-----.++++++++++++.--[----->++<]>-.-[-->+++<]>--.>++++
++++++.[->+++<]>++........+++.---.[-->+++++<]>--.-[--->+<]>.+++++.+++[->+++<]>.--[--->+<]>-.---[->++++<]>.------------.-
------.--[--->+<]>-.[---->+<]>+++.++[->+++<]>.+++++++++.+++.[-->+++++<]>+++.---[->++++<]>-.----------.++++.+++.----.---.
------.++++++.+++++++++++.+++++.-[-->+++++<]>.------------.--[->++++<]>-.[->+++<]>.--[--->+<]>-.+[->+++<]>+.+++++++++++.
-.[++>---<]>++.[->+++<]>-.[---->+<]>+++.[->+++<]>+.-[++>-----<]>..----.-[--->+<]>.-[---->+<]>++.[->+++<]>+.-[->+++<]>.+[
----->+<]>.------------.--[--->+<]>--.--------.-[++>---<]>+.-[--->++<]>--.---.+++++++++++++.-------------.[->+++<]>-.>++
++++++++.[->+++<]>++........+++.---.>-[--->+<]>-.[---->+++++<]>-.+.++++++++++.+[---->+<]>+++.+[----->+<]>.--------.----.
+++++++++++++.+++++.+[---->+<]>+++.---[->++++<]>.------------.-------.--[--->+<]>-.[---->+<]>+++.-[--->++<]>-.---.[--->+
<]>--.--[-->+++++<]>.---[->++++<]>.-[--->++<]>-.++++++++++.+[---->+<]>+++.+[----->+<]>+.+.+++++.[---->+<]>+++.[->+++<]>+
.-[->+++<]>.+[----->+<]>.++++++++.---------.++++++++.-----------.+++++++.----.-------.--[--->+<]>-.+++++[->+++<]>.------
---.[--->+<]>--.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[
----->+<]>.+[->+++++<]>+.[--->+++++<]>++.[->++++<]>.>++++++++++.[->+++<]>++........+++.---.---[->++++<]>.------------.+.
++++++++++.+[---->+<]>+++.--[->++++<]>-.+[->+++<]>+.+++..[++>---<]>--.[->+++<]>+.++..++.[--->+<]>----..+[---->+<]>+++.++
+++[->+++<]>.++++++.-.[++>---<]>-.--[----->+<]>.---------.--[->+++<]>+.-[--->+<]>--.+++++++++++++.++++++.-------.-------
---.--[--->+<]>---.+[---->+<]>+++.+[----->+<]>.--------.++++++++.++.+++.+++++++.-[---->+<]>++.[->+++<]>+.+++++++++++++.-
---------.-[--->+<]>-.[-->+++++++<]>.++.---.-----------.--[--->+<]>-.+[->+++<]>+.++.--[--->+<]>-.[->+++<]>+.++++++++++++
+.>++++++++++.[->+++<]>++........+++.---.+[->+++<]>++.+++++++++++++..---.+++.[-->+++++<]>+++.+++++[->+++<]>.+++.[-->++++
+<]>+++.++++++++.[->+++<]>-.--------.+++.+.++++[->+++<]>.--[--->+<]>.++++++++.---------.-[--->++<]>-.+++++.-----------.+
+++++++++++.+++..-------------.--.-[--->+<]>--.[---->+<]>+++.---[----->++<]>.-------------.[--->+<]>----.++.---------.++
++++++.-.+[++>---<]>.>++++++++++.[->+++<]>++........[->+++<]>+.-[->+++<]>.-[->++<]>-.+[-->+<]>+.---[->++++<]>.--------.[
-->+<]>--------.--[-->+++++<]>--.+++.--------------.+++.-[->+++<]>-.--[--->+<]>-.--.---[->++++<]>.++++.--.+.-[--->+<]>++
+.>++++++++++.[->+++<]>++........[->+++<]>++.--[->+++<]>.-[->++<]>-.+[-->+<]>+.---[->++++<]>.--------.[-->+<]>--------.-
-[-->+++++<]>--.+++.--------------.+++.-[->+++<]>-.--[--->+<]>.---.---[->++++<]>.++++.--.+.-[--->+<]>+++.>++++++++++.[->
+++<]>++........+++.---.---[->+++<]>.++[->++++<]>+.--[--->+<]>-.[->+++<]>+.++..-[--->+<]>-.--------.++++++++.---------.-
----------.--[--->+<]>-.+++[->+++<]>.--[--->+<]>-.[->+++<]>+.+++++++++++.+++.-.-------.-[--->+<]>--.---[->++++<]>.------
------.---.--[--->+<]>-.--[-->+++++<]>.---[->++++<]>.+[->+++<]>+.+++++.++++.--------.+++++++++.+++++.----------.++++++.-
.>++++++++++.[->+++<]>++........[->+++<]>+.++..-[--->+<]>-.--------.++++++++.---------.-----------.--[--->+<]>-.-----.++
+.[-->+++++<]>+++.+++++++++++.-[-->+++<]>--.+[-->+<]>+.---[->++++<]>.--------.[-->+<]>--------.--[--->+<]>.+++++++++++.+
++++.+[--->+<]>+.--[--->+<]>-.[--->++++<]>.------------.[->+++<]>++.+[->+++<]>.>++++++++++.[->+++<]>++........+++.---.[-
>++<]>+.+[-->+++<]>+.--[--->+<]>.[->+++<]>-.+++++++++++++.-----------.++.--[--->+<]>-.---[->++++<]>.------------.---.--[
--->+<]>-.[-->+++++++<]>.++++.--.+.+[---->+<]>+++.---[->++++<]>.-----.[--->+<]>-----.---[->++++<]>.------------.---.--[-
-->+<]>-.+[----->+<]>+.---------.[--->+<]>+.----.[---->+<]>+++.--[-->+++++<]>.---[->++++<]>.[->+++<]>++.++++++++++.+++.-
-----------.++++++++.>++++++++++.[->+++<]>++........[->+++<]>+.--.---[->++++<]>.++++.--.+.+[---->+<]>+++.+++++++++++.-[-
->+++<]>--.+[-->+<]>+.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++
<]>.-[----->+<]>.+[->+++++<]>+.[--->+++++<]>++.---[->++++<]>.++++++++++.----------.---[->++++<]>-.+.--.---------.-----.+
.------.++.++++++++++.>++++++++++.[->+++<]>++........[->+++<]>++.---.---[->++++<]>.++++.--.+.+[---->+<]>+++.+++++++++++.
-[-->+++<]>--.+[-->+<]>+.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->++
+++<]>.-[----->+<]>.+[->+++++<]>+.[--->+++++<]>++.---[->++++<]>.++++++++++.----------.---[->++++<]>-.+.--.---------.----
-.+.------.+++.+++++++++.>++++++++++.[->+++<]>++....+++.---.--[->++++<]>+.----------.++++++.-[---->+<]>+++.+[->+++<]>.--
.+++++++++++++.-[->+++++<]>-.++[->+++<]>.-[--->+<]>--.--.++++[->+++<]>.--[--->+<]>-.[->+++<]>+.--[--->+<]>---.++++[->+++
<]>.+++++++.+++++++++++.--.+++[->+++<]>++.--[--->+<]>---.+++++++.-[---->+<]>++.[->+++<]>+.++.-[--->+<]>--.-----------.[-
>++++++<]>.[->+++<]>-.--[--->+<]>-.-----------.++++++.-.-[->+++++<]>-.++[->+++<]>.-[--->+<]>--.-------.-----------.-[---
>+<]>--.-----------.++++++.-.+++++.+[---->+<]>+++.-[--->++<]>--.---.+++++++++++++.-------------.>++++++++++.[->+++<]>++.
...+++.---.--[->++++<]>-.+[->+++<]>.+.+++.-------.--[--->+<]>-.---[->++++<]>.------------.---.--[--->+<]>-.[->+++<]>+.++
..-[--->+<]>-.--------.++++++++.---------.-----------.--[--->+<]>-.-----.+++.[-->+++++<]>+++.-[--->++<]>-.++++++++++.+[-
--->+<]>+++.---[->++++<]>-.+.-----------.+++..[++>---<]>--.-[--->++<]>-.+++++.-[->+++++<]>-.+++[->++<]>.++++++++++.>-[--
--->+<]>.-.+[--->++<]>-.[--->+<]>-.[->+++<]>++....-[--->++<]>-.---.[--->+<]>--.[->++<]>+.++.>-[--->+<]>-.-----------.>+[
--->++<]>.++[---->+++<]>-.>-[--->+<]>-.-----------.++++++.-.[->++++<]>++.>++++++++++.[->+++<]>++........[->+++<]>+.++..-
[--->+<]>-.--------.++++++++.---------.-----------.--[--->+<]>-.-----.+++.[-->+++++<]>+++.-[->++<]>-.+[-->+<]>+.[->++<]>
+.++.>-[--->+<]>-.-----------.>+[--->++<]>.++[---->+++<]>-.>-[--->+<]>-.-----------.++++++.-.[-->+<]>+.--[--->+<]>-.++..
-[--->+<]>-.--------.++++++++.---------.-----------.--[--->+<]>-.-----.+++.[--->+<]>+++.>++++++++++.[->+++<]>++....+[->+
++<]>.[--->+<]>-.-[->++<]>-.+[-->+<]>+.[->+++<]>+.++..-[--->+<]>-.--------.++++++++.---------.-----------.--[--->+<]>-.-
----.+++.++[++>---<]>.[--->++<]>.-----.+[++>---<]>.-[->+++<]>-.--------.[-->+<]>--------.+[--->+<]>+.++++++.+++.--------
------.--[--->+<]>-.++[++>---<]>.+++++.-------------.>++++++++++..[->+++<]>++....+++.---.--[-->+++<]>...................
........................................>++++++++++.[->+++<]>++....+++.---.---[->+++<]>.-[--->+<]>.---------.+++++++++++
.+++[->+++<]>.--[--->+<]>-.[->+++<]>++.-.++.++++++++.-[++>---<]>+.---[->++++<]>.------------.---.--[--->+<]>-.[->+++<]>+
+.++++++++++.+++.------------.++++++++.-[++>---<]>+.+++++[->+++<]>.---------.[--->+<]>--.---[->++++<]>.------------.---.
--[--->+<]>-.+++++[->+++<]>.++++++.-.----.+++++.-.[---->+<]>+++.+[----->+<]>.------------.--[--->+<]>-.--.---------.-[--
->+<]>.[---->+<]>++.+[->++<]>+.>++++++++++.[->+++<]>++....+++++[->+++<]>.---------..+++++++++++++.++[->+++<]>.++++.+++++
+++++.[->+++++<]>-.-[->++<]>-.+[-->+<]>+.[-->+++++++<]>.-------.-----.-----.++++++++++++++.[->+++++<]>-.++++++++++.-----
-----.+[->++<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>
.+[->+++++<]>+.[----->++++<]>+.-----[->++++<]>.+++++++++++.-----------.---[->++++<]>.--------.[-->+<]>--------.++[->++<]
>+.--[--->+<]>---.+++[->+++<]>++.+++++++++++++.-------.--.--[->+++<]>-.++++++++.----.------------.+[->++<]>.++++++++++.+
++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[----->++++<]
>+.+[-->+<]>++.>++++++++++.[->+++<]>++....+++++[->+++<]>.---------..+++++++++++++.++[->+++<]>.++++.+++++++++++.-[->+++++
<]>-.-[->++<]>-.+[-->+<]>+.[-->+++++++<]>.-------.-----.-----.+++++++++++++++.-[->+++++<]>-.++++++++++.----------.+[->++
<]>.++++++++++.+++.[----->+<]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]
>+.[--------->++<]>.++[----->++<]>.+++++++++++.-----------.---[->++++<]>.--------.[-->+<]>--------.++[->++<]>+.--[--->+<
]>---.+++[->+++<]>++.+++++++++++++.-------.--.--[->+++<]>-.++++++++.----.------------.+[->++<]>.++++++++++.+++.[----->+<
]>.++++++++.--[----->+++<]>.------------.----------.-[---->+++++<]>.-[----->+<]>.+[->+++++<]>+.[--------->++<]>.[-->+<]>
++.>++++++++++.[->+++<]>++....+[->+++<]>.----.---[->++++<]>.++++.--.+.+[---->+<]>+++.-[->++<]>-.+[-->+<]>+.+[->+++<]>.--
--.---[->++++<]>.++++.--.[-->+++++<]>+++.+++++++++++.-----------.---[->++++<]>-.+.--.---------.-----.+.------.++++.+++++
+++++.[->+++++<]>-.++++++++++.----------.+++++[->+++<]>.---------..+++++++++++++.++[->+++<]>.++++.++++++++++.>+[--->++<]
>+++++.-[--->++<]>--.++[->+++++<]>.------------.[-->+++++<]>--.-[--->+<]>.-.---------.--------.[--->+<]>+.+++++++++++.--
---------.---[->++++<]>-.+.--.---------.-----.+.------.++++.+++++++++++.-[->+++++<]>-.++++++++++.----------.+++++[->+++<
]>.---------..+++++++++++++.++[->+++<]>.++++.+++++++++++.+[------->+<]>++.-------------.-[--->+<]>.-.---------.-[->+++<]
>.------------.---[->++<]>.[->++++++<]>+.>++++++++++.[->+++<]>++....+[->+++<]>.----.++++++++++++++.------------.--[--->+
<]>--.--------.-[++>---<]>+.-[->++<]>-.+[-->+<]>+.++++++++.[--->++<]>-.---------..+++++++++++++.++[->+++<]>.++++.+++++++
+++.>+[--->++<]>+++++.-[--->++<]>--.++[->+++++<]>.------------.[-->+++++<]>--.-[--->+<]>.-.---------.--------.[--->+<]>+
.--[->++<]>.[-->+<]>++.++++++[->++<]>+.+[-->+<]>++.---------.++++++.------.++++++++.[--->++<]>-.---------..+++++++++++++
.++[->+++<]>.++++.+++++++++++.+[------->+<]>++.-------------.-[--->+<]>.-.---------.-[->+++<]>.------------.---[->++<]>.
[->++++++<]>+.[--->+<]>+.--[->++<]>.[-->+<]>++.[-->+++++<]>--.[-->+<]>++.>++++++++++.[->+++<]>++....---[->++++<]>.------
--.[-->+<]>--------.[--->++<]>-.+.-----.+++.-------------.--[->+++<]>-.+[--->+<]>.----.---[->++++<]>.++++.--.+.-[++>---<
]>+.------------.+[->+++<]>.+[->+++<]>.------------.+[----->+<]>.------------.--[--->+<]>--.--------.-[->+++<]>-.--[->++
++++<]>+.----.++++++++++++++.------------.--[--->+<]>--.--------.--[----->++<]>-.
"""

BLOCK_M = 128
BLOCK_N = 128
BLOCK_K = 32
matmul_kernel = triton.compile(src, signature="*f16,*f16,*f16,i32,i32,i32,i32,i32,i32",
                                constants={7: 1, 9: 1, 11: 1, 12: BLOCK_M, 13: BLOCK_N, 14: BLOCK_K, 
                                           15: 8, 16: None})


# %%
# We can now create a convenience wrapper function that only takes two input tensors
# and (1) checks any shape constraint; (2) allocates the output; (3) launches the above kernel


def matmul(a, b, activation=None):
    # checks constraints
    assert a.shape[1] == b.shape[0], "incompatible dimensions"
    assert a.is_contiguous(), "matrix A must be contiguous"
    assert b.is_contiguous(), "matrix B must be contiguous"
    M, K = a.shape
    K, N = b.shape
    assert (
        K % 32 == 0
    ), "We don't check memory-out-of-bounds with K so K must be divisible by BLOCK_SIZE_K"
    # allocates output
    c = torch.empty((M, N), device=a.device, dtype=a.dtype)
    # 1D launch kernel where each block gets its own program.
    grid = (triton.cdiv(M, BLOCK_M) * triton.cdiv(N, BLOCK_N), )
    matmul_kernel[grid](
        a, b, c,
        M, N, K,
        a.stride(0),
        b.stride(0),
        c.stride(0),
    )
    return c


# %%
# Unit Test
# ---------
#
# We can test our custom matrix multiplication operation against a native torch implementation (i.e., cuBLAS)

torch.manual_seed(0)
a = torch.randn((512, 512), device='cuda', dtype=torch.float16)
b = torch.randn((512, 512), device='cuda', dtype=torch.float16)
triton_output = matmul(a, b, activation=None)
torch_output = torch.matmul(a, b)
print(f"triton_output={triton_output}")
print(f"torch_output={torch_output}")
if torch.allclose(triton_output, torch_output, atol=1e-2, rtol=0):
    print("✅ Triton and Torch match")
else:
    print("❌ Triton and Torch differ")

# %%
# Benchmark
# ---------
#
# Square Matrix Performance
# ~~~~~~~~~~~~~~~~~~~~~~~~~~
#
# We can now compare the performance of our kernel against that of cuBLAS. Here we focus on square matrices, but feel free to arrange this script as you wish to benchmark any other matrix shape.


@triton.testing.perf_report(
    triton.testing.Benchmark(
        x_names=['M', 'N', 'K'],  # argument names to use as an x-axis for the plot
        x_vals=[
            8192
        ],  # different possible values for `x_name`
        line_arg='provider',  # argument name whose value corresponds to a different line in the plot
        # possible values for `line_arg``
        line_vals=['cublas', 'triton'],
        # label name for the lines
        line_names=["cuBLAS", "Triton"],
        # line styles
        styles=[('green', '-'), ('green', '--'), ('blue', '-'), ('blue', '--')],
        ylabel="TFLOPS",  # label name for the y-axis
        plot_name="matmul-performance",  # name for the plot. Used also as a file name for saving the plot.
        args={},
    )
)
def benchmark(M, N, K, provider):
    a = torch.randn((M, K), device='cuda', dtype=torch.float16)
    b = torch.randn((K, N), device='cuda', dtype=torch.float16)
    if provider == 'cublas':
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: torch.matmul(a, b), rep=100)
    if provider == 'triton':
        ms, min_ms, max_ms = triton.testing.do_bench(lambda: matmul(a, b), rep=100)
    perf = lambda ms: 2 * M * N * K * 1e-12 / (ms * 1e-3)
    return perf(ms), perf(max_ms), perf(min_ms)


benchmark.run(show_plots=True, print_data=True)
