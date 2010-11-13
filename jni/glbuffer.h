#ifndef glbuffer_h_seen
#define glbuffer_h_seen

#include <jni.h>
#define UNUSED  __attribute__((unused))
void native_start(JNIEnv *env, jclass clazz);
void native_gl_resize(JNIEnv *env, jclass clazz, jint w, jint h);
void native_gl_render(JNIEnv *env, jclass clazz);
#endif
