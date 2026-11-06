# Robot Motor Inertia Matching: Screen Gear Ratios in Python

The [full WIFA Robotics lesson](https://wifarobotics.com/learn/robot-motor-inertia-matching/) explains how a reducer can lower reflected load inertia while raising motor speed and, past a point, acceleration torque.

## Start with an empty computer

1. Install Python 3.12 or newer from [python.org](https://www.python.org/downloads/). On Windows, verify with `py -3 --version`; on macOS or Linux use `python3 --version`. On Linux you can also use your distribution's Python package.
2. On this GitHub page choose **Code**, then **Download ZIP**. Extract the folder. Open PowerShell or Terminal, then run `cd "path to the extracted folder"`. Run `dir` on Windows or `ls` on macOS/Linux. You should see `sweep.py`, `examples` and `tests`.
3. Run the commands below. Use `py -3` instead of `python3` on Windows. The lab and tests need no pip packages.

```sh
python3 sweep.py examples/reference.json
python3 sweep.py examples/heavier-payload.json
python3 sweep.py examples/speed-conflict.json
python3 -m unittest discover -s tests -v
```

The first case passes 10:1 and 20:1. Of those two, 10:1 takes less modeled acceleration torque: 0.195 N·m versus 0.210 N·m. The heavier case passes 15:1, 20:1 and 25:1, with 20:1 taking the least at 0.285 N·m. The speed conflict has no passing ratio and returns exit code 0 because it is a valid calculation. `python3 sweep.py examples/reversed-ratio.json` intentionally returns exit code 2: a 10:1 reducer is entered as 10, not 0.1.

## Make one change

Copy `reference.json` to `examples/my-axis.json`. Add 12 and 13 to the ratio list, leaving the other values alone, and run the new file. The modeled torque minimum lies near 12.65:1. Real reducers are discrete; a candidate must exist and meet the supplier's mechanical and speed limits before it is useful.

Inertias are mass moments in kg·m², not kg and not a force moment. Multiply kg·cm² by 0.0001 to obtain kg·m². The gear inertia field is already at the motor side; never divide it by the ratio again or count it in the output load. Use nonnegative inertia values, positive speed and acceleration magnitudes, distinct reductions of 1:1 or higher, and the same JSON keys as the reference case. The entered acceleration cap and inertia limit are scenario inputs, not universal limits.

If Python cannot open the input, check your current folder. If the file fails to parse, check quotation marks, decimal points and trailing commas. If every ratio fails, read the individual screen flags before changing a limit.

## Project files

* `sweep.py`: calculator and command line interface.
* `examples/`: three working scenarios and one deliberate input error.
* `tests/test_sweep.py`: hand calculation, kinetic energy and virtual work checks, plus limits and input tests.
* `diagrams/`: editable SVG sources and matching WebPs. The shaft diagram separates motor side and load side speeds. The torque plot shows the rising motor side share and falling reflected output share. To regenerate both, install Inkscape on your PATH and Pillow in a virtual environment, then run `python3 diagrams/render.py` with DejaVu Sans installed. Rendering is optional.

## Where the model stops

This is an offline screening model for one ideal rigid axis and a fixed output speed and acceleration magnitude. It assumes the same gear input inertia for each candidate in a file. It does not model changing arm poses, gearbox efficiency, gravity, friction, compliance, brake sizing, motor thermal duty, or a drive's torque at each speed. A passing row authorizes no physical test and does not size a motor. Use the actual reducer inertia per ratio, a worst case pose and the manufacturer's torque versus speed data, duty limits and commissioning procedure.

References: [Yaskawa servo motor sizing concepts](https://www.yaskawa.com/delegate/getAttachment?cmd=documents&documentId=PR.DN.01&documentName=PR.DN.01.pdf), [Oriental Motor sizing calculations](https://www.orientalmotor.com/technology/motor-sizing-calculations.html), and [Python unittest](https://docs.python.org/3.12/library/unittest.html).
