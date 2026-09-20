from manim import *


class TestAnimation(Scene):
    def construct(self):
        circle = Circle()

        self.play(Create(circle))
        self.wait(1)

        self.play(circle.animate.shift(RIGHT * 2))
        self.wait(1)

        self.play(circle.animate.set_color(RED))
        self.wait(1)