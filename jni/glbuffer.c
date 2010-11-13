#include <GLES/gl.h>
#include <GLES/glext.h>
#include <android/log.h>
#include <pthread.h>
#include <string.h>
#include "glbuffer.h"

#define TEXTURE_WIDTH 512
#define TEXTURE_HEIGHT 256
#define LOG_TAG "GLBUFEX"
#define LOGI(...)  __android_log_print(ANDROID_LOG_INFO,LOG_TAG,__VA_ARGS__)
#define S_PIXELS_SIZE (sizeof(s_pixels[0]) * TEXTURE_WIDTH * TEXTURE_HEIGHT)
#define RGB565(r, g, b)  (((r) << (5+6)) | ((g) << 6) | (b))

static uint16_t *s_pixels = 0;
static pthread_cond_t s_vsync_cond;
static pthread_mutex_t s_vsync_mutex;
static GLuint s_texture = 0;
static int s_x = 10;
static int s_y = 50;


static void check_gl_error(const char* op)
{
	GLint error;
	for (error = glGetError(); error; error = glGetError())
		LOGI("after %s() glError (0x%x)\n", op, error);
}

/* wait for the screen to redraw */
static void wait_vsync()
{
	pthread_mutex_lock(&s_vsync_mutex);
	pthread_cond_wait(&s_vsync_cond, &s_vsync_mutex);
	pthread_mutex_unlock(&s_vsync_mutex);
}

static void render_pixels(uint16_t *pixels)
{
	int x, y;
	/* fill in a square of 5 x 5 at s_x, s_y */
	for (y = s_y; y < s_y + 5; y++) {
		for (x = s_x; x < s_x + 5; x++) {
			int idx = x + y * TEXTURE_WIDTH;
			pixels[idx++] = RGB565(31, 31, 0);
		}
	}
}

int s_w = 0;
int s_h = 0;

/* disable these capabilities. */
static GLuint s_disable_caps[] = {
	GL_FOG,
	GL_LIGHTING,
	GL_CULL_FACE,
	GL_ALPHA_TEST,
	GL_BLEND,
	GL_COLOR_LOGIC_OP,
	GL_DITHER,
	GL_STENCIL_TEST,
	GL_DEPTH_TEST,
	GL_COLOR_MATERIAL,
	0
};

void native_gl_resize(JNIEnv *env UNUSED, jclass clazz UNUSED, jint w, jint h)
{
	LOGI("native_gl_resize %d %d", w, h);
	glDeleteTextures(1, &s_texture);
	GLuint *start = s_disable_caps;
	while (*start)
		glDisable(*start++);
	glEnable(GL_TEXTURE_2D);
	glGenTextures(1, &s_texture);
	glBindTexture(GL_TEXTURE_2D, s_texture);
	glTexParameterf(GL_TEXTURE_2D,
			GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	glTexParameterf(GL_TEXTURE_2D,
			GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glShadeModel(GL_FLAT);
	check_gl_error("glShadeModel");
	glColor4x(0x10000, 0x10000, 0x10000, 0x10000);
	check_gl_error("glColor4x");
	int rect[4] = {0, TEXTURE_HEIGHT, TEXTURE_WIDTH, -TEXTURE_HEIGHT};
	glTexParameteriv(GL_TEXTURE_2D, GL_TEXTURE_CROP_RECT_OES, rect);
	check_gl_error("glTexParameteriv");
	s_w = w;
	s_h = h;
}

void native_gl_render(JNIEnv *env UNUSED, jclass clazz UNUSED)
{
	memset(s_pixels, 0, S_PIXELS_SIZE);
	render_pixels(s_pixels);
	glClear(GL_COLOR_BUFFER_BIT);
	glTexImage2D(GL_TEXTURE_2D,		/* target */
			0,			/* level */
			GL_RGB,			/* internal format */
			TEXTURE_WIDTH,		/* width */
			TEXTURE_HEIGHT,		/* height */
			0,			/* border */
			GL_RGB,			/* format */
			GL_UNSIGNED_SHORT_5_6_5,/* type */
			s_pixels);		/* pixels */
	check_gl_error("glTexImage2D");
	glDrawTexiOES(0, 0, 0, s_w, s_h);
	check_gl_error("glDrawTexiOES");
	/* tell the other thread to carry on */
	pthread_cond_signal(&s_vsync_cond);
}

void native_start(JNIEnv *env UNUSED, jclass clazz UNUSED)
{
	/* init conditions */
	pthread_cond_init(&s_vsync_cond, NULL);
	pthread_mutex_init(&s_vsync_mutex, NULL);
	int incr = 1;
	s_pixels = malloc(S_PIXELS_SIZE);
	while (1) {
		/* draw a square going backwards and forwards */
		s_x += incr;
		if (s_x > 200)
			incr = -1;
		if (s_x < 20 && incr < 0)
			incr = 1;
		/* wait on screen sync */
		wait_vsync();
	}
}
