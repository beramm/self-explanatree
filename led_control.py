from luma.core.interface.serial import spi, noop
from luma.core.render import canvas
from luma.led_matrix.device import max7219
import time
import logging


class EyeAnimation:
    LEFT_EYE_X = 2
    RIGHT_EYE_X = 11
    EYE_WIDTH = 3

    def __init__(self, port=0, device_id=0, cascaded=2,
                 rotate=0, width=16, height=8, contrast=100,
                 reinit_interval_minutes=5):

        self.port = port
        self.device_id = device_id
        self.cascaded = cascaded
        self.rotate = rotate
        self.width = width
        self.height = height
        self.contrast = contrast
        self.reinit_interval_minutes = reinit_interval_minutes

        self.serial = None
        self.device = None
        self.last_init_time = None
        
        self.current_expression = "neutral"
        self.blink_interval = 3          # detik antar kedip
        self.last_blink_time = time.time()

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(self.__class__.__name__)

    def set_expression(self, mode):
        allowed = ["neutral", "sad", "angry", "happy"]
        if mode in allowed:
            self.current_expression = mode
    
    # =============================
    # SPI MANAGEMENT
    # =============================

    def init_spi(self):
        try:
            self.logger.info("Menginisialisasi SPI...")
            self.serial = spi(port=self.port, device=self.device_id, gpio=noop())
            self.device = max7219(
                self.serial,
                cascaded=self.cascaded,
                rotate=self.rotate,
                width=self.width,
                height=self.height,
                contrast=self.contrast
            )
            self.device.clear()
            time.sleep(0.5)

            self.last_init_time = time.time()
            self.logger.info("SPI berhasil diinisialisasi")
            return True

        except Exception as e:
            self.logger.error(f"Gagal inisialisasi SPI: {e}")
            self.serial = None
            self.device = None
            return False

    def cleanup_spi(self):
        try:
            if self.device:
                try:
                    self.device.clear()
                except:
                    pass
                try:
                    self.device.cleanup()
                except:
                    pass
        finally:
            self.serial = None
            self.device = None
            time.sleep(0.5)

    def should_reinit(self):
        if self.last_init_time is None:
            return True
        elapsed_minutes = (time.time() - self.last_init_time) / 60
        return elapsed_minutes >= self.reinit_interval_minutes

    # =============================
    # DRAWING SECTION
    # =============================

    def draw_eyes(self, draw, top, height):
        for x in range(self.EYE_WIDTH):
            for y in range(height):
                draw.point((self.LEFT_EYE_X + x, top + y), fill="white")
                draw.point((self.RIGHT_EYE_X + x, top + y), fill="white")

    def draw_eyebrows(self, draw, mode="neutral"):
        if mode == "neutral":
            for y in [1]:
                draw.line((self.LEFT_EYE_X, y, self.LEFT_EYE_X + 2, y), fill="white")
                draw.line((self.RIGHT_EYE_X, y, self.RIGHT_EYE_X + 2, y), fill="white")

        elif mode == "angry":
            draw.line((self.LEFT_EYE_X-1, 2, self.LEFT_EYE_X + 2, 0), fill="white")
            # draw.line((self.LEFT_EYE_X-1, 3, self.LEFT_EYE_X + 2, 1), fill="white")
            draw.line((self.RIGHT_EYE_X, 0, self.RIGHT_EYE_X + 3, 2), fill="white")
            # draw.line((self.RIGHT_EYE_X, 1, self.RIGHT_EYE_X + 3, 3), fill="white")

        elif mode == "surprised":
            for y in [0, 1]:
                draw.line((self.LEFT_EYE_X, y, self.LEFT_EYE_X + 2, y), fill="white")
                draw.line((self.RIGHT_EYE_X, y, self.RIGHT_EYE_X + 2, y), fill="white")

        elif mode == "sad":
            draw.line((self.LEFT_EYE_X, 1, self.LEFT_EYE_X + 3, 3), fill="white")
            draw.line((self.RIGHT_EYE_X-1, 3, self.RIGHT_EYE_X + 2, 1), fill="white")

    def animate(self):
        if self.device is None:
            raise RuntimeError("Device belum diinisialisasi")

        now = time.time()

        # Cek apakah waktunya kedip
        blinking = False
        if now - self.last_blink_time >= self.blink_interval:
            blinking = True
            self.last_blink_time = now

        # Mata terbuka normal
        with canvas(self.device) as draw:
            if blinking:
                # self.draw_eyes(draw, top=4, height=2)  # terbuka
                # time.sleep(0.15)
                self.draw_eyes(draw, top=5, height=1)  # tertutup

            else:
                self.draw_eyes(draw, top=4, height=3)  # terbuka
                

            self.draw_eyebrows(draw, self.current_expression)

        if blinking:
            time.sleep(0.15)
                
    # =============================
    # ANIMATION
    # =============================

    def run_animation(self):
        if self.device is None:
            raise RuntimeError("Device tidak terinisialisasi")

        with canvas(self.device) as draw:
            self.draw_eyes(draw, top=3, height=3)
            self.draw_eyebrows(draw, "neutral")
        time.sleep(1.2)

        with canvas(self.device) as draw:
            self.draw_eyes(draw, top=4, height=2)
            self.draw_eyebrows(draw, "neutral")
        time.sleep(0.15)

        with canvas(self.device) as draw:
            self.draw_eyes(draw, top=5, height=1)
            self.draw_eyebrows(draw, "neutral")
        time.sleep(0.15)

        with canvas(self.device) as draw:
            self.draw_eyes(draw, top=4, height=2)
            self.draw_eyebrows(draw, "neutral")
        time.sleep(0.15)

    # =============================
    # MAIN LOOP
    # =============================

    def start(self):
        while not self.init_spi():
            self.logger.warning("Retry inisialisasi dalam 2 detik...")
            time.sleep(2)

        while True:
            try:
                if self.should_reinit():
                    self.logger.info("Reinit berkala...")
                    self.cleanup_spi()
                    time.sleep(1)
                    while not self.init_spi():
                        time.sleep(2)

                # self.run_animation()

                self.animate()
                time.sleep(0.05)  # frame delay kecil supaya smooth

            except KeyboardInterrupt:
                self.logger.info("Program dihentikan user")
                self.cleanup_spi()
                break

            except Exception as e:
                self.logger.error(f"Error: {type(e).__name__}: {e}")
                self.cleanup_spi()
                time.sleep(2)

                while not self.init_spi():
                    time.sleep(3)

                time.sleep(1)


# =============================
# ENTRY POINT
# =============================

if __name__ == "__main__":
    eyes = EyeAnimation()
    
    import threading
    threading.Thread(target=eyes.start).start()
    
    while True:
        eyes.set_expression("sad")
        time.sleep(5)
        eyes.set_expression("angry")
        time.sleep(5)
        eyes.set_expression("neutral")
        time.sleep(5)