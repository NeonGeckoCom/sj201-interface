# SJ-201 Interface
Contains Python bindings for released versions of the SJ201 using 
[Mycroft testing code](https://github.com/MycroftAI/mark-ii-hardware-testing)
for reference.

# CLI Usage

## `sj201 reset-led <color>`
Chase the specified color and then chase off LED ring. Valid colors are:
- white
- yellow
- red
- green
- blue
- magenta
- burnt_orange
- mycroft_red
- mycroft_green
- mycroft_blue
>*NOTE*: On the SJ201R10, this command must be run as root

## `sj201 set-fan-speed <percent>`
Set the fan speed to the specified speed as a percentage.
>*NOTE*: On the SJ201R10, changing the fan speed is currently not persistent and
> the fan will default to 100%. This command should only be used for validating
> that the fan changes to the set value momentarily.

## `init-ti-amp`
Perform one-time initialization of the TAS5806 Audio Amplifier
