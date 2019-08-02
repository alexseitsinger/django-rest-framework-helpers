<a name="v7.0.2"></a>
## [v7.0.2](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v7.0.1...v7.0.2) (2019-08-02)

### Bug Fixes
- Fixes expanding for nested objs. ([f6a7439](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/f6a743929d524573dd0a932ac059900283fe10f6))


<a name="v7.0.1"></a>
## [v7.0.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v7.0.0...v7.0.1) (2019-08-01)

### Bug Fixes
- None to [] to prevent exception. ([ae05126](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/ae05126ac5843a8dd767f31cf717200fcf6c64e4))
- Returns None if object is empty. ([8b2d2f7](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/8b2d2f757f6772b54f464d5f659da50d29e49366))

### Code Refactoring
- Uses local var instead of direct asign. ([ae72998](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/ae729987cff2cb6c3b703f3582320d02c9c7fdcf))


<a name="v7.0.0"></a>
## [v7.0.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v6.0.1...v7.0.0) (2019-07-31)

### Code Refactoring
- Moves expandable modules. ([731a6ab](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/731a6ab8f4c30785318323748db6d60ad6898823))
- Movex expandable to own sub-package. ([fe48d41](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/fe48d41a027072631ec9030b211746d0a4039af0))

### Features
- Adds more util modules. ([c756a28](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/c756a286164aab9cd3b3c975e8e89c09fcb7f6a8))


<a name="v6.0.1"></a>
## [v6.0.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v6.0.0...v6.0.1) (2019-07-30)

### Bug Fixes
- Gets nested object expanding working. ([2ddfbe9](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/2ddfbe9ea0bc9930b8d63e7b52a094063d9fe93b))

### Features
- Adds utils for expanding. ([987bb5b](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/987bb5b2b151a851e970fdc78fb9cfdd8ce85f0a))


<a name="v6.0.0"></a>
## [v6.0.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v5.3.0...v6.0.0) (2019-07-26)

### Bug Fixes
- Replaces renamed ExpandableRelatedField. ([6a57448](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/6a5744811d14c2667c6623f8889db9e1f598a669))

### Features
- Adds & updates mixins. ([c2187a7](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/c2187a7c60ef7f2f4a9ccbcf5dcddb263ad995db))
- Adds & updates various util methods. ([40edc1f](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/40edc1f89d9d11753731928fabe05d62d83b1468))


<a name="v5.3.0"></a>
## [v5.3.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v5.2.1...v5.3.0) (2019-07-23)

### Bug Fixes
- Correctly expands multiple fields. ([7bcdc04](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/7bcdc04873226aeb687f98e3c45e046472af13f0))

### Code Refactoring
- Removes default suffix from APIRootView. ([01498cb](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/01498cbf009bd8ff1c6b22d5356d31eb5a071100))
- Removes unnecessary print statement. ([8e82b35](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/8e82b353327a337773098acda25395ccc52cf1ba))

### Features
- Adds util for removing redundant paths. ([8bed2da](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/8bed2da2134fa773d52ac5eec1c8cefb0b3a7534))


<a name="v5.2.1"></a>
## [v5.2.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v5.2.0...v5.2.1) (2019-07-22)

### Bug Fixes
- Fixes wrong endpoints response. ([8bcb14f](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/8bcb14f9895bb915f7052d105651308733fd7276))


<a name="v5.2.0"></a>
## [v5.2.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v5.1.0...v5.2.0) (2019-07-22)

### Code Refactoring
- Reformats endpoint mixins. ([c8ea3aa](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/c8ea3aac0b5473576dcb11ecc22dcf5aa44e47ec))
- Renames variables and methods. ([c5033c7](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/c5033c7f8bfd2a9e0e60f55fea09cdd03952b5eb))
- Updates APIRootView. ([d73a2d0](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/d73a2d072790553d1181a7bee8861c994fd0833b))

### Features
- Adds APIRootView mixins. ([c8bd351](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/c8bd351f6bfb03475419dc79e674de5a808a9aef))
- Adds view name formatting. ([cf91061](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/cf910616d23cbc46abea564f9f5f7b3c30170199))


<a name="v5.1.0"></a>
## [v5.1.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v5.0.0...v5.1.0) (2019-07-22)

### Features
- Adds default permissions for mixin. ([dcb4454](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/dcb4454d7d1a1c312f1b37b855565c650d05e377))


<a name="v5.0.0"></a>
## [v5.0.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v4.0.2...v5.0.0) (2019-07-22)

### Features
- Renames ExpandableField. ([6cc97b7](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/6cc97b740f3ce649c51622927e1ed35c71663be1))


<a name="v4.0.2"></a>
## [v4.0.2](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v4.0.1...v4.0.2) (2019-07-22)

### Bug Fixes
- Fixes getters for action mixins. ([2808fbd](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/2808fbd530618a1f6f0fe2d484f18cb633a84229))


<a name="v4.0.1"></a>
## [v4.0.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v4.0.0...v4.0.1) (2019-07-22)

### Bug Fixes
- Fixes self.action check. ([962b4a1](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/962b4a1b50e04e7300cd29f95b5690c2ebf2aec3))


<a name="v4.0.0"></a>
## [v4.0.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v3.1.0...v4.0.0) (2019-07-22)

### Code Refactoring
- Deletes Base64ImageField. ([363edaf](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/363edaf4845db9a4cfb53174d85f54ac97b7ff53))
- Deletes routers module. ([a48933a](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/a48933abb813a82dc4d80644285391517f4e9938))
- Fixes import for action maps. ([0a80c51](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/0a80c51ea60b8ba976604aab5b6be55a9c7cf267))
- Moved action maps to utils. ([3ad029e](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/3ad029e0154f00ff665eaaed6cd859febec4bdd7))


<a name="v3.1.0"></a>
## [v3.1.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v3.0.0...v3.1.0) (2019-07-22)

### Features
- Adds Expandable mixin and field. ([6c2261c](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/6c2261c7925c0726792e866489b29797010f96eb))
- Adds new mixin. ([4f53bb4](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/4f53bb48d4e30e344095bcc9aaef53ed3d6e038b))
- Adds new util methods. ([e5b0344](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/e5b03445583d4b182c635018c47a356c805e64e1))


<a name="v3.0.0"></a>
## [v3.0.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v2.1.0...v3.0.0) (2019-07-20)

### Code Refactoring
- Changes API for Expandable field spec. ([37f551a](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/37f551a4785340ad52562f50f5d32a834eb0ae25))


<a name="v2.1.0"></a>
## [v2.1.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v2.0.4...v2.1.0) (2019-07-20)

### Code Refactoring
- Removed silent errors for `load_urls`. ([930f70b](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/930f70b67b3894f618ccc8c245e3ef5318fdec19))

### Features
- Adds nested expansion for fields. ([257fa3d](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/257fa3d4d7413e130bf7a06a35bbbe057ac9f565))


<a name="v2.0.4"></a>
## [v2.0.4](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v2.0.3...v2.0.4) (2019-07-20)

### Bug Fixes
- Adds HashableDict for reppresentation output. ([beaaa6b](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/beaaa6b1264b14411f2d1f64c03a99f3c7a8470b))

### Features
- Adds utils module. ([c312489](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/c312489ac8cbc8fcffccab1a87ab6cf461c99999))


<a name="v2.0.3"></a>
## [v2.0.3](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v2.0.2...v2.0.3) (2019-07-19)

### Bug Fixes
- Fix getattr for request. ([672e719](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/672e719c63308a7b589bee2c50e8c32f9994e26d))


<a name="v2.0.2"></a>
## [v2.0.2](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v2.0.1...v2.0.2) (2019-07-19)

### Bug Fixes
- Makes expand serializer dynamic. ([20057e2](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/20057e237c4bf19fac76a5401e91e9d9c61b0f25))


<a name="v2.0.1"></a>
## [v2.0.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v2.0.0...v2.0.1) (2019-07-16)

### Bug Fixes
- Fixes overwriting expand_serializer at init. ([ab14722](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/ab147225ebd366124b31baa698f17a5251b1aef9))


<a name="v2.0.0"></a>
## [v2.0.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v1.1.2...v2.0.0) (2019-07-16)

### Features
- Adds fields module. ([0a56317](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/0a5631747c063d6df2f173ba186c731016789205))


<a name="v1.1.2"></a>
## [v1.1.2](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v1.1.1...v1.1.2) (2019-07-15)

### Bug Fixes
- Fixes http url normalization. ([24e853e](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/24e853e54660a63f76459da29be47755e86f1ed7))


<a name="v1.1.1"></a>
## [v1.1.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v1.1.0...v1.1.1) (2019-07-15)

### Bug Fixes
- Fixes allowed referers permission. ([612e7e7](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/612e7e7960a0602b651646c5fc10f1cc771e28d6))


<a name="v1.1.0"></a>
## [v1.1.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v1.0.1...v1.1.0) (2019-07-15)

### Features
- Adds `load_urls` method. ([cc5b065](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/cc5b06596f5ff33d01692759b89b9f1c62e086e5))


<a name="v1.0.1"></a>
## [v1.0.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v1.0.0...v1.0.1) (2019-07-15)

### Bug Fixes
- Fixes missing colon. ([260057d](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/260057d806ab5768483be66d54bdd1a174587374))


<a name="v1.0.0"></a>
## [v1.0.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v0.2.2...v1.0.0) (2019-07-15)

### Code Refactoring
- Deletes empty module. ([52e41e9](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/52e41e974d5c005245356c14badb7e00b6a37f27))

### Features
- Adds/updates permission classes. ([523d2ac](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/523d2ac92e3ea03935eb69be6fe022c3aea7d96a))


<a name="v0.2.2"></a>
## [v0.2.2](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v0.2.1...v0.2.2) (2019-06-29)


<a name="v0.2.1"></a>
## [v0.2.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v0.1.1...v0.2.1) (2019-06-29)

### Bug Fixes
- Fixes regex typo. ([74fbee1](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/74fbee1766e931e6850283556223951f1e64e0b9))
- Fixes typo in ignored string. ([a9d5f0e](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/a9d5f0eeef407f71e80f25ed85abf7caff98d7e6))

### Code Refactoring
- Renames package. ([db1cc2d](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/db1cc2dd70fdc812b534ad63b3b7739aa628d81e))
- Updates serializers and mixins modules. ([8b43016](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/8b430167274dcce95b9e6ef242acacde4393e4ac))

### Features
- Adds LoadableImageField. ([7e82bc1](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/7e82bc1d15a4b13063354c1662b9098a97c6a40d))
- Adds new mixin. ([3635d98](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/3635d9824fc7617ef1d86776749a6c91184df6fd))
- Adds routes and views modules. ([eef72a8](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/eef72a80c2b6d6975997e58623f5034745ba2ae8))


<a name="v0.1.1"></a>
## [v0.1.1](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/v0.1.0...v0.1.1) (2019-06-29)

### Code Refactoring
- Updates urls module. ([d305c52](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/d305c52408a29947a4db1612c3df3e61caa83542))

### Features
- Adds urls module. ([691afce](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/691afce38f86edc3dbfbfbcce73848c78a52c628))


<a name="v0.1.0"></a>
## [v0.1.0](https://github.com/alexseitsinger/django-rest-framework-helpers/compare/8ccc9195f8dfdf803193d60e87bcf1e5294dcad2...v0.1.0) (2019-06-29)

### Features
- Initial commit, master. ([8ccc919](https://github.com/alexseitsinger/django-rest-framework-helpers/commit/8ccc9195f8dfdf803193d60e87bcf1e5294dcad2))


