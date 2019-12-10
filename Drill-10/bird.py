import game_framework
from pico2d import *
import game_world

# Boy Run Speed
# fill expressions correctly
PIXEL_PER_METER = (10.0 / 0.3)
RUN_SPEED_KMPH = 20.0
RUN_SPEED_MPM = (RUN_SPEED_KMPH * 1000.0 / 60.0)
RUN_SPEED_MPS = (RUN_SPEED_MPM * 60.0)
RUN_SPEED_PPS = (RUN_SPEED_KMPH * PIXEL_PER_METER)

# Boy Action Speed
# fill expressions correctly
TIME_PER_ACTION = 0.5
ACTION_PER_TIME = 1.0 / TIME_PER_ACTION
FRAMES_PER_ACTION = 8

# Boy Event
RIGHT_DOWN, LEFT_DOWN, RIGHT_UP, LEFT_UP, SLEEP_TIMER, SPACE = range(6)

key_event_table = {
    (SDL_KEYDOWN, SDLK_RIGHT): RIGHT_DOWN,
    (SDL_KEYDOWN, SDLK_LEFT): LEFT_DOWN,
    (SDL_KEYUP, SDLK_RIGHT): RIGHT_UP,
    (SDL_KEYUP, SDLK_LEFT): LEFT_UP,
    (SDL_KEYDOWN, SDLK_SPACE): SPACE
}


# Boy States

class IdleState:

    @staticmethod
    def enter(bird, event):
        bird.velocity = RUN_SPEED_PPS


    @staticmethod
    def exit(bird, event):
        if event == SPACE:
            bird.fire_ball()
        pass

    @staticmethod
    def do(bird):
        bird.calculate_frame()
        bird.x += bird.velocity * game_framework.frame_time
        bird.x = clamp(25, bird.x, 1600 - 25)

        if bird.x > get_canvas_width() - 100:
            bird.velocity = -RUN_SPEED_PPS
        elif bird.x < 100:
            bird.velocity = RUN_SPEED_PPS
        bird.dir = clamp(-1, bird.velocity, 1)

    @staticmethod
    def draw(bird):
        if bird.dir == 1:
            bird.image.clip_draw(int(bird.frame) * bird.width, bird.now_row * bird.height, bird.width, bird.height, bird.x,
                                bird.y)
        else:
            bird.image.clip_composite_draw(int(bird.frame) * bird.width, bird.now_row * bird.height, bird.width, bird.height,
                                          0, 'h', bird.x, bird.y, bird.width, bird.height)


class RunState:

    @staticmethod
    def enter(bird, event):
        if event == RIGHT_DOWN:
            bird.velocity += RUN_SPEED_PPS
        elif event == LEFT_DOWN:
            bird.velocity -= RUN_SPEED_PPS
        elif event == RIGHT_UP:
            bird.velocity -= RUN_SPEED_PPS
        elif event == LEFT_UP:
            bird.velocity += RUN_SPEED_PPS
        bird.dir = clamp(-1, bird.velocity, 1)

    @staticmethod
    def exit(bird, event):
        if event == SPACE:
            bird.fire_ball()

    @staticmethod
    def do(bird):
        bird.calculate_frame()
        bird.x += bird.velocity * game_framework.frame_time
        bird.x = clamp(25, bird.x, 1600 - 25)

    @staticmethod
    def draw(bird):
        if bird.dir == 1:
            bird.image.clip_draw(int(bird.frame) * bird.width, bird.now_row * bird.height, bird.width, bird.height, bird.x,
                                bird.y)
        else:
            bird.image.clip_composite_draw(int(bird.frame) * bird.width, bird.now_row * bird.height, bird.width, bird.height,
                                          0, 'h', bird.x, bird.y, bird.width, bird.height)


class SleepState:

    @staticmethod
    def enter(bird, event):
        bird.frame = 0

    @staticmethod
    def exit(bird, event):
        pass

    @staticmethod
    def do(bird):
        bird.calculate_frame()

    @staticmethod
    def draw(bird):
        if bird.dir == 1:
            bird.image.clip_composite_draw(int(bird.frame) * 100, 300, 100, 100, 3.141592 / 2, '', bird.x - 25, bird.y - 25,
                                          100, 100)
        else:
            bird.image.clip_composite_draw(int(bird.frame) * 100, 200, 100, 100, -3.141592 / 2, '', bird.x + 25,
                                          bird.y - 25, 100, 100)


next_state_table = {
    IdleState: {RIGHT_UP: RunState, LEFT_UP: RunState, RIGHT_DOWN: RunState, LEFT_DOWN: RunState,
                SLEEP_TIMER: SleepState, SPACE: IdleState},
    RunState: {RIGHT_UP: IdleState, LEFT_UP: IdleState, LEFT_DOWN: IdleState, RIGHT_DOWN: IdleState, SPACE: RunState},
    SleepState: {LEFT_DOWN: RunState, RIGHT_DOWN: RunState, LEFT_UP: RunState, RIGHT_UP: RunState, SPACE: IdleState}
}


class Bird:
    def __init__(self):
        self.x, self.y = 1600 // 2, 150
        # Boy is only once created, so instance image loading is fine
        self.image = load_image('bird_animation.png')
        self.height = int(self.image.h / 3) - 1
        self.width = int(self.image.w / 5) - 1
        self.now_row = 2
        self.font = load_font('ENCR10B.TTF', 16)
        self.dir = 1
        self.velocity = 0
        self.frame = 0
        self.event_que = []
        self.cur_state = IdleState
        self.cur_state.enter(self, None)
        self.cnt = True

    def calculate_frame(self):
        if self.now_row == 0:
            self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 4
        else:
            self.frame = (self.frame + FRAMES_PER_ACTION * ACTION_PER_TIME * game_framework.frame_time) % 5
        if int(self.frame) > 0:
            self.cnt = True
        if int(self.frame) == 0 and self.cnt:
            if self.now_row == 2:
                self.now_row = 1
            elif self.now_row == 1:
                self.now_row = 0
            elif self.now_row == 0:
                self.now_row = 2
            self.cnt = False

    def add_event(self, event):
        self.event_que.insert(0, event)

    def update(self):
        self.cur_state.do(self)
        if len(self.event_que) > 0:
            event = self.event_que.pop()
            self.cur_state.exit(self, event)
            self.cur_state = next_state_table[self.cur_state][event]
            self.cur_state.enter(self, event)

    def draw(self):
        self.cur_state.draw(self)
        self.font.draw(self.x - 60, self.y + 50, '(TIme: %3.2f)' % get_time(), (255, 255, 0))

    def handle_event(self, event):
        if (event.type, event.key) in key_event_table:
            key_event = key_event_table[(event.type, event.key)]
            self.add_event(key_event)
