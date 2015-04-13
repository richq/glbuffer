package com.example.glbuffer;

import javax.microedition.khronos.opengles.GL10;
import javax.microedition.khronos.egl.EGLConfig;
import android.util.Log;
import android.opengl.GLSurfaceView;
import android.os.SystemClock;
import android.content.Context;
import android.util.AttributeSet;

public class GlBufferView extends GLSurfaceView {
	private static native void native_start();
	private static native void native_gl_resize(int w, int h);
	private static native void native_gl_render();

	public GlBufferView(Context context, AttributeSet attrs) {
		super(context, attrs);
		(new Thread() {
			@Override
			public void run() {
				native_start();
			}
		}).start();
		setRenderer(new MyRenderer());
		requestFocus();
		setFocusableInTouchMode(true);
	}

	class MyRenderer implements GLSurfaceView.Renderer {
		@Override
		public void onSurfaceCreated(GL10 gl, EGLConfig c) { /* do nothing */ }

		@Override
		public void onSurfaceChanged(GL10 gl, int w, int h) {
			native_gl_resize(w, h);
		}

		@Override
		public void onDrawFrame(GL10 gl) {
			time = SystemClock.uptimeMillis();

			if (time >= (frameTime + 1000.0f)) {
				frameTime = time;
				avgFPS += framerate;
				framerate = 0;
			}

			if (time >= (fpsTime + 3000.0f)) {
				fpsTime = time;
				avgFPS /= 3.0f;
				Log.d("GLBUFEX", "FPS: " + Float.toString(avgFPS));
				avgFPS = 0;
			}
			framerate++;
			native_gl_render();
		}
		public long time = 0;
		public short framerate = 0;
		public long fpsTime = 0;
		public long frameTime = 0;
		public float avgFPS = 0;
	}

	static {
		System.loadLibrary("glbuffer");
	}
}
