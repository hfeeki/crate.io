import slumber

from django.core.cache import cache
from django.utils.safestring import mark_safe

from evaluator import suite

from packages.models import ReadTheDocsPackageSlug
from packages.utils import verlib


class PEP386Compatability(object):
    title = "PEP386 Compatibility"
    message = mark_safe("PEP386 defines a specific allowed syntax for Python package versions."
                "<br /><br />"
                "Previously it was impossible to accurately determine across any Python package what "
                "order the versions should go in, but with PEP386 we can now intelligently sort by version..."
                "<br /><br />"
                "But only if the version numbers are compatible!")

    def evaluate(self, release):
        normalized = verlib.suggest_normalized_version(release.version)

        if release.version == normalized:
            # Release Is Already Normalized
            return {
                "level": "success",
                "message": mark_safe('Compatible with <a href="http://www.python.org/dev/peps/pep-0386/">PEP386</a>.'),
            }
        elif normalized is not None:
            # Release Isn't Normalized, But We Can Figure It Out
            return {
                "level": None,
                "message": mark_safe('Almost Compatible with <a href="http://www.python.org/dev/peps/pep-0386/">PEP386</a>.'),
            }
        else:
            # We Can't Normalize the Release Version
            return {
                "level": "error",
                "message": mark_safe('Incompatible with <a href="http://www.python.org/dev/peps/pep-0386/">PEP386</a>.'),
            }


class PackageHosting(object):
    title = "Package Hosting"
    message = mark_safe("Did you know that packages listed on PyPI aren't required to host there?"
                "<br /><br />"
                "When your package manager tries to install a package from PyPI it looks in number "
                "of locations, one such location is an author specified url of where the package can "
                "be downloaded from."
                "<br /><br />"
                "Packages hosted by the author means that installing this package depends on the "
                "authors server staying up, adding another link in the chain that can cause your "
                "installation to fail")

    def evaluate(self, release):
        if release.files.all().exists():
            return {
                "level": "success",
                "message": "Package is hosted on PyPI",
            }
        elif release.download_uri:
            return {
                "level": "error",
                "message": "Package isn't hosted on PyPI",
            }
        else:
            return {
                "level": "error",
                "message": "No Package Hosting",
            }


class RTDDocs(object):
    title = "Documentation hosted on Read The Docs"
    message = mark_safe("Documentation can be one of the most important parts of any library."
                "Even more important than just having documentation, is making sure that people are "
                "able to find it easily."
                "<br /><br />"
                "Read The Docs is an open source platform for hosting documentation generated by Sphinx."
                "<br /><br />"
                "Hosting your documentation on Read The Docs is easy (even if it's just an additional copy), and "
                "it allows people who want to use your package the ability to locate your documentation in "
                "what is quickly becoming a one stop shop for online open source documentation."
                "<br /><br />"
                "<small>If this says you aren't hosted on Read The Docs and you are please contact "
                "<a href='mailto:support@crate.io'>support@crate.io</a></small>")

    def evaluate(self, release):
        qs = ReadTheDocsPackageSlug.objects.filter(slug=release.package.name)
        slug = qs[0].slug if qs else release.package.name

        key = "evaluate:rtd:%s" % slug

        if cache.get(key) is not None:
            hosted_on_rtd = cache.get(key)
        else:
            api = slumber.API(base_url="http://readthedocs.org/api/v1/")
            results = api.project.get(slug=slug)

            if results["objects"]:
                hosted_on_rtd = True
            else:
                hosted_on_rtd = False

            cache.set(key, hosted_on_rtd, 60 * 60 * 24 * 7)  # Cache This for a Week

        if hosted_on_rtd:
            return {
                "level": "success",
                "message": mark_safe('Docs Available on <a href="http://readthedocs.org/">Read The Docs</a>'),
            }
        else:
            return {
                "level": "error",
                "message": mark_safe('Docs Unavailable on <a href="http://readthedocs.org/">Read The Docs</a>')
            }


suite.register(PEP386Compatability)
suite.register(PackageHosting)
suite.register(RTDDocs)
