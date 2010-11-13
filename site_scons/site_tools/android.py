#!/usr/bin/env python
import os
from SCons.Builder import Builder
from SCons.Defaults import DirScanner
from xml.dom import minidom

def get_rfile(fname):
     p = minidom.parse(open(fname))
     m = p.getElementsByTagName('manifest')[0]
     return os.path.join(m.getAttribute('package').replace('.', '/'), 'R.java')

def get_target_version(fname):
     p = minidom.parse(open(fname))
     m = p.getElementsByTagName('uses-sdk')[0]
     return m.getAttribute('android:minSdkVersion')

def AndroidApp(env, name, manifest='#/AndroidManifest.xml',
              source='src', resources='#/res',
              native_folder='libs'):
    android_manifest = env.File(manifest)

    env['ANDROID_TARGET'] = get_target_version(android_manifest.abspath)
    env['ANDROID_JAR'] = '$ANDROID_SDK/platforms/android-$ANDROID_TARGET/android.jar'
    rfile = os.path.join('gen', get_rfile(android_manifest.abspath))
    gen = env.Dir('gen')

    # generate R.java
    r = env.Aapt(rfile, env.Dir(resources),
             source_scanner=DirScanner,
             MANIFEST=android_manifest.path,
             GEN=gen, RES=env.Dir(resources).abspath,
             AAPT_ARGS='''package -f -m
             -M $MANIFEST
             -S $RES
             -I $ANDROID_JAR
             -J $GEN'''.split())
    env.Depends(r, android_manifest)

    # compile java to classes
    bin_classes = 'bin/classes'
    classes = env.Java(target=bin_classes, source=[source],
                       JAVABOOTCLASSPATH='$ANDROID_JAR',
                       JAVASOURCEPATH=gen.path,
                       JAVACFLAGS='-g -encoding ascii'.split(),
                       JAVACLASSPATH=env.Dir(bin_classes).path)
    env.Depends(classes, rfile)

    # dex file from classes
    dex = env.Dex('classes.dex', classes, DX_DIR=env.Dir(bin_classes).path)

    # resources
    ap = env.Aapt(name + '.ap_', [env.Dir(resources)],
                  source_scanner=DirScanner,
                  MANIFEST=android_manifest.path,
                  RES=env.Dir(resources).abspath,
              AAPT_ARGS='''package -f -m
             -M $MANIFEST
             -S $RES
             -I $ANDROID_JAR
             -F $TARGET'''.split())
    env.Depends(ap, android_manifest)

    # package java -classpath jarutils.jar:androidprefs.jar:apkbuilder.jar com.android.apkbuilder.ApkBuilder
    # >> name-debug-unaligned.apk
    outname = name + '-debug-unaligned.apk'
    finalname = name + '-debug.apk'
    if env['ANDROID_KEY_STORE']:
        UNSIGNED='-u'
        outname = name + '-unsigned.apk'
        finalname = name + '.apk'
    else:
        UNSIGNED = ''
    unaligned = env.ApkBuilder(outname, env.Dir(native_folder),
                   source_scanner=DirScanner,
                   NATIVE_FOLDER=env.Dir(native_folder).path,
                   UNSIGNED=UNSIGNED,
                   DEX=dex,
                   AP=ap,
                   APK_ARGS='''
                   $UNSIGNED
                   -f $DEX
                   -z $AP
                   -nf $NATIVE_FOLDER
                  '''.split())
    env.Depends(unaligned, [dex, ap])
    if env['ANDROID_KEY_STORE'] and env['ANDROID_KEY_NAME']:
        # jarsigner -keystore $ANDROID_KEY_STORE -signedjar $TARGET $SOURCE $ANDROID_KEY_NAME
        unaligned = env.JarSigner(name + '-unaligned.apk', unaligned)

    # zipalign -f 4 unaligned aligned
    return env.ZipAlign(finalname, unaligned)

def Tools(env, tools):
    for t in tools:
        env.Tool(t)

def GetVariable(env, variable, exit=True):
    if variable in os.environ:
        return os.environ[variable]
    elif variable in env:
        return env[variable]
    elif exit:
        print 'Please set %s. export %s=path' % (variable, variable)
        print "or run `scons %s=path'" % variable
        env.Exit(1)
    return None

def generate(env, **kw):
    ndk_path = GetVariable(env, 'ANDROID_NDK')
    sdk_path = GetVariable(env, 'ANDROID_SDK')

    env['ANDROID_KEY_STORE'] = ''
    env['ANDROID_KEY_NAME'] = ''

    gnu_tools = ['gcc', 'g++', 'gnulink', 'ar', 'gas', 'javac']
    Tools(env, gnu_tools)

    env['ANDROID_GCC_VERSION'] = '4.4.0'
    ndk_bin = os.path.join(ndk_path, 'build/prebuilt/linux-x86/arm-eabi-$ANDROID_GCC_VERSION/bin/')
    env.PrependENVPath('PATH', env.subst(ndk_bin))
    ARM_PREFIX = 'arm-eabi-'

    env['CC'] = ARM_PREFIX+'gcc'
    env['CXX'] = ARM_PREFIX+'g++'
    env['AS'] = ARM_PREFIX+'as'
    env['AR'] = ARM_PREFIX+'ar'
    env['RANLIB'] = ARM_PREFIX+'ranlib'
    env['OBJCOPY'] = ARM_PREFIX+'objcopy'
    env['PROGSUFFIX'] = '.elf'

    env['AAPT'] = '$ANDROID_SDK/platforms/android-$ANDROID_TARGET/tools/aapt'
    env['DX'] = '$ANDROID_SDK/platforms/android-$ANDROID_TARGET/tools/dx'
    env['ZIPALIGN'] = '$ANDROID_SDK/tools/zipalign'
    env['JARSIGNER'] = 'jarsigner'

    bld = Builder(action='$AAPT $AAPT_ARGS', suffix='.java')
    env.Append(BUILDERS = { 'Aapt': bld })

    bld = Builder(action='$DX --dex --output=$TARGET $DX_DIR', suffix='.dex')
    env.Append(BUILDERS = { 'Dex': bld })
    env['JAVA'] = 'java'

    cpfiles = os.pathsep.join(os.path.join('$ANDROID_SDK', 'tools/lib', jar)
                              for jar in 'jarutils.jar androidprefs.jar apkbuilder.jar'.split())

    env['APK_BUILDER_CP'] = cpfiles
    bld = Builder(action='$JAVA -classpath $APK_BUILDER_CP com.android.apkbuilder.ApkBuilder $TARGET $APK_ARGS', suffix='.apk')
    env.Append(BUILDERS = { 'ApkBuilder': bld })

    bld = Builder(action='$ZIPALIGN -f 4 $SOURCE $TARGET')
    env.Append(BUILDERS = { 'ZipAlign': bld })

    bld = Builder(action='$JARSIGNER -keystore $ANDROID_KEY_STORE -signedjar $TARGET $SOURCE $ANDROID_KEY_NAME')
    env.Append(BUILDERS = { 'JarSigner': bld })

    env['CPPPATH'] = '$ANDROID_NDK/build/platforms/android-$ANDROID_TARGET/arch-arm/usr/include'

    env['CFLAGS'] = '''-Wall -Wextra -fpic -mthumb-interwork -ffunction-sections
    -funwind-tables -fstack-protector -fno-short-enums -D__ARM_ARCH_5__
    -D__ARM_ARCH_5T__ -D__ARM_ARCH_5E__ -D__ARM_ARCH_5TE__  -Wno-psabi
    -march=armv5te -mtune=xscale -msoft-float -mthumb -Os -fomit-frame-pointer
    -fno-strict-aliasing -finline-limit=64 -DANDROID -Wa,--noexecstack'''.split()

    env['LIBPATH'] = '$ANDROID_NDK/build/platforms/android-$ANDROID_TARGET/arch-arm/usr/lib'
    env['ANDROID_LIBS'] = '-lc -llog'
    env['SHLINKFLAGS'] = '''-nostdlib -Wl,-soname,$TARGET -Wl,-shared,-Bsymbolic
    -Wl,--whole-archive  -Wl,--no-whole-archive
    $ANDROID_LIBS
    -Wl,--no-undefined -Wl,-z,noexecstack'''.split()

    env.AddMethod(AndroidApp)

def exists(env):
    return 1
