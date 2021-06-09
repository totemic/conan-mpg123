from conans import AutoToolsBuildEnvironment, CMake, ConanFile, tools
from conans.errors import ConanInvalidConfiguration
import os


class Mpg123Conan(ConanFile):
    name = "mpg123"
    version = "1.25.10"
    debian_build_version = "2" 
    description = "Fast console MPEG Audio Player and decoder library"
    topics = ("conan", "mpg123", "mpeg", "audio", "player", "decoder")
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "http://mpg123.org/"
    license = "LGPL-2.1-or-later", "GPL-2.0-or-later"
    settings = "os", "compiler", "build_type", "arch"
    options = {
        # "shared": [True, False],
        # "fPIC": [True, False],
        # "flexible_resampling": [True, False],
        # "network": [True, False],
        # "icy": [True, False],
        # "id3v2": [True, False],
        # "ieeefloat": [True, False],
        # "layer1": [True, False],
        # "layer2": [True, False],
        # "layer3": [True, False],
        # "moreinfo": [True, False],
        # "seektable": "ANY"
        # "module": ["dummy", "libalsa", "tinyalsa", "win32", "coreaudio"],
    }
    default_options = {
        # "shared": True,
        # "fPIC": True,
        # "flexible_resampling": True,
        # "network": True,
        # "icy": True,
        # "id3v2": True,
        # "ieeefloat": True,
        # "layer1": True,
        # "layer2": True,
        # "layer3": True,
        # "moreinfo": True,
        # "seektable": "1000",
        # "module": "coreaudio",
    }
    fixed_options = {
        "shared": False,
        "fPIC": False,
        "flexible_resampling": True,
        "network": True,
        "icy": True,
        "id3v2": True,
        "ieeefloat": True,
        "layer1": True,
        "layer2": True,
        "layer3": True,
        "moreinfo": True,
        "seektable": "1000",
        "module": "coreaudio",
    }
    exports_sources = "CMakeLists.txt", "patches/**"
    generators = "cmake", "pkg_config", "cmake_find_package"

    _autotools = None
    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd
        # if self.options.shared:
        #     del self.options.fPIC
        try:
            int(self.fixed_options["seektable"])
        except ValueError:
            raise ConanInvalidConfiguration("seektable must be an integer")
        if self.settings.os != "Windows":
            if self.options == "win32":
                raise ConanInvalidConfiguration("win32 is an invalid module for non-Windows os'es")

    def requirements(self):
        if self.settings.os == "Linux":
            self.requires("libasound2/1.1.8@totemic/stable")
            # if self.options.module == "libalsa":
            #     self.requires("libalsa/1.2.4")
            # if self.options.module == "tinyalsa":
            #     self.requires("tinyalsa/1.1.1")

    def build_requirements(self):
        if self.settings.os != "Linux":
            self.build_requires("pkgconf/1.7.3")
            self.build_requires("yasm/1.3.0")
            if tools.os_info.is_windows and self.settings.compiler != "Visual Studio" and not tools.get_env("CONAN_BASH_PATH"):
                self.build_requires("msys2/20200517")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename("mpg123-{}".format(self.version), self._source_subfolder)

    @property
    def _audio_module(self):
        # return {
        #     "libalsa": "alsa",
        # }.get(str(self.options.module), str(self.options.module))
        if self.settings.os == "Linux":
            return "alsa"
        elif self.settings.os == "Windows":
            return "win32"
        elif self.settings.os == "Macos":
            return "coreaudio"


    def _configure_autotools(self):
        if self._autotools:
            return self._autotools
        self._autotools = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)
        yes_no = lambda v: "yes" if v else "no"
        conf_args = [
            "--enable-moreinfo={}".format(yes_no(self.fixed_options["moreinfo"])),
            "--enable-network={}".format(yes_no(self.fixed_options["network"])),
            "--enable-ntom={}".format(yes_no(self.fixed_options["flexible_resampling"])),
            "--enable-icy={}".format(yes_no(self.fixed_options["icy"])),
            "--enable-id3v2={}".format(yes_no(self.fixed_options["id3v2"])),
            "--enable-ieeefloat={}".format(yes_no(self.fixed_options["ieeefloat"])),
            "--enable-layer1={}".format(yes_no(self.fixed_options["layer1"])),
            "--enable-layer2={}".format(yes_no(self.fixed_options["layer2"])),
            "--enable-layer3={}".format(yes_no(self.fixed_options["layer3"])),
            "--with-audio={}".format(self._audio_module),
            "--with-seektable={}".format(self.fixed_options["seektable"]),
            "--enable-modules=no",
            "--enable-shared={}".format(yes_no(self.fixed_options["shared"])),
            "--enable-static={}".format(yes_no(not self.fixed_options["shared"])),
        ]
        self._autotools.configure(args=conf_args, configure_dir=self._source_subfolder)
        return self._autotools

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["NO_MOREINFO"] = not self.fixed_options["moreinfo"]
        self._cmake.definitions["NETWORK"] = self.fixed_options["network"]
        self._cmake.definitions["NO_NTOM"] = not self.fixed_options["flexible_resampling"]
        self._cmake.definitions["NO_ICY"] = not self.fixed_options["icy"]
        self._cmake.definitions["NO_ID3V2"] = not self.fixed_options["id3v2"]
        self._cmake.definitions["IEEE_FLOAT"] = self.fixed_options["ieeefloat"]
        self._cmake.definitions["NO_LAYER1"] = not self.fixed_options["layer1"]
        self._cmake.definitions["NO_LAYER2"] = not self.fixed_options["layer2"]
        self._cmake.definitions["NO_LAYER3"] = not self.fixed_options["layer3"]
        self._cmake.definitions["USE_MODULES"] = False
        self._cmake.definitions["CHECK_MODULES"] = self._audio_module
        self._cmake.definitions["WITH_SEEKTABLE"] = self.fixed_options["seektable"]
        self._cmake.verbose = True
        self._cmake.parallel = False
        self._cmake.configure()
        return self._cmake

    def translate_arch(self):
        arch_names = {"x86_64": "amd64",
                        "x86": "i386",
                        "ppc32": "powerpc",
                        "ppc64le": "ppc64el",
                        "armv7": "arm",
                        "armv7hf": "armhf",
                        "armv8": "arm64",
                        "s390x": "s390x"}
        return arch_names[str(self.settings.arch)]
        
    def _download_extract_deb(self, url, sha256):
        filename = "./download.deb"
        deb_data_file = "data.tar.xz"
        tools.download(url, filename)
        tools.check_sha256(filename, sha256)
        # extract the payload from the debian file
        self.run("ar -x %s %s" % (filename, deb_data_file))
        os.unlink(filename)
        tools.unzip(deb_data_file)
        os.unlink(deb_data_file)

    def triplet_name(self):
        # we only need the autotool class to generate the host variable
        autotools = AutoToolsBuildEnvironment(self)

        # construct path using platform name, e.g. usr/lib/arm-linux-gnueabihf/pkgconfig
        # if not cross-compiling it will be false. In that case, construct the name by hand
        return autotools.host or get_gnu_triplet(str(self.settings.os), str(self.settings.arch), self.settings.get_safe("compiler"))

    def build(self):
        if self.settings.os == "Linux":
            if self.settings.arch == "x86_64":
                # https://packages.debian.org/buster/libmpg123-0
                sha_lib = "aad76b14331161db35a892d211f892e8ceda7e252a05dca98b51c00ae59d1b33"
                # https://packages.debian.org/buster/amd64/libout123-0/download
                sha_out = "319060bdf4a17f0b9d876c6ed3d87e7458d262864c7cac7fc7c46796fe06cded"
                # https://packages.debian.org/buster/libmpg123-dev
                sha_dev = "ac90ec3a573dbddbb663d6565fe9985a5d9c994509ac6b11168ed980e964d58f"

            elif self.settings.arch == "armv8":
                # https://packages.debian.org/buster/arm64/libmpg123-0/download
                sha_lib = "f6a7a962e87229af47f406449dc6837d0383be76752180ea22da17c1318e1aae"
                # https://packages.debian.org/buster/arm64/libout123-0/download
                sha_out = "4cb138ec6e20cf66857c2ca69c3914b4c9e74fc8287271fd741608af421528eb"
                # https://packages.debian.org/buster/arm64/libmpg123-dev/download
                sha_dev = "4b5312bc0a8f3a1cb765ff8f3d3d1af1fddcaf05aa723314fbc0277ba6ea43ff"
            else: # armv7hf
                raise Exception("Add urls paths for specified linux architecture")

            #http://ftp.us.debian.org/debian/pool/main/m/mpg123/libmpg123-0_1.25.10-2_amd64.deb
            #http://ftp.us.debian.org/debian/pool/main/m/mpg123/libmpg123-0_1.25.10-2_arm64.deb
            #http://ftp.us.debian.org/debian/pool/main/m/mpg123/libout123-0_1.25.10-2_amd64.deb
            #http://ftp.us.debian.org/debian/pool/main/m/mpg123/libout123-0_1.25.10-2_arm64.deb
            #http://ftp.us.debian.org/debian/pool/main/m/mpg123/libmpg123-dev_1.25.10-2_amd64.deb
            #http://ftp.us.debian.org/debian/pool/main/m/mpg123/libmpg123-dev_1.25.10-2_arm64.deb
            url_lib = ("http://ftp.us.debian.org/debian/pool/main/m/mpg123/libmpg123-0_%s-%s_%s.deb"
                % (str(self.version), self.debian_build_version, self.translate_arch()))
            url_out = ("http://ftp.us.debian.org/debian/pool/main/m/mpg123/libout123-0_%s-%s_%s.deb"
                % (str(self.version), self.debian_build_version, self.translate_arch()))
            url_dev = ("http://ftp.us.debian.org/debian/pool/main/m/mpg123/libmpg123-dev_%s-%s_%s.deb"
                % (str(self.version), self.debian_build_version, self.translate_arch()))

            self._download_extract_deb(url_lib, sha_lib)
            self._download_extract_deb(url_out, sha_out)
            self._download_extract_deb(url_dev, sha_dev)

        else:
            for patch in self.conan_data.get("patches", {}).get(self.version, []):
                tools.patch(**patch)
            if self.settings.compiler == "Visual Studio":
                cmake = self._configure_cmake()
                cmake.build()
            else:
                autotools = self._configure_autotools()
                autotools.make()

    def package(self):
        if self.settings.os == "Linux":
            self.copy(pattern="*", dst="lib", src="usr/lib/" + self.triplet_name(), symlinks=True)
            self.copy(pattern="*", dst="include", src="usr/include", symlinks=True)
            self.copy(pattern="copyright", src="usr/share/doc/" + self.name, symlinks=True)
        else:
            self.copy("COPYING", src=self._source_subfolder, dst="licenses")
            if self.settings.compiler == "Visual Studio":
                cmake = self._configure_cmake()
                cmake.install()
            else:
                autotools = self._configure_autotools()
                autotools.install()

            tools.remove_files_by_mask(os.path.join(self.package_folder, "lib"), "*.la")
            tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
            tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
            tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.filenames["cmake_find_package"] = "mpg123"
        self.cpp_info.filenames["cmake_find_package_multi"] = "mpg123"
        self.cpp_info.names["cmake_find_package"] = "MPG123"
        self.cpp_info.names["cmake_find_package_multi"] = "MPG123"

        self.cpp_info.components["libmpg123"].libs = ["mpg123"]
        self.cpp_info.components["libmpg123"].names["pkg_config"] = "libmpg123"
        if self.settings.os == "Windows" and self.fixed_options["shared"]:
            self.cpp_info.components["libmpg123"].defines.append("LINK_MPG123_DLL")

        self.cpp_info.components["libout123"].libs = ["out123"]
        self.cpp_info.components["libout123"].names["pkg_config"] = "libout123"
        self.cpp_info.components["libout123"].requires = ["libmpg123"]

        # self.cpp_info.components["libsyn123"].libs = ["syn123"]
        # self.cpp_info.components["libsyn123"].names["pkg_config"] = "libsyn123"
        # self.cpp_info.components["libsyn123"].requires = ["libmpg123"]

        if self.settings.os == "Linux":
            self.cpp_info.components["libmpg123"].system_libs = ["m"]
            self.cpp_info.components["libout123"].requires.append("libasound2::libasound2")
            
            #if self.options.module == "libalsa":
            ##    self.cpp_info.components["libout123"].requires.append("libalsa::libalsa")
            #if self.options.module == "tinyalsa":
            #    self.cpp_info.components["libout123"].requires.append("tinyalsa::tinyalsa")

        elif self.settings.os == "Windows":
            self.cpp_info.components["libmpg123"].system_libs = ["shlwapi"]
            self.cpp_info.components["libout123"].system_libs.append("winmm")
        elif self.settings.os == "Macos":
            self.cpp_info.components["libout123"].libs.append("-Wl,-framework,AudioToolbox")
