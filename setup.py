import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    install_requires = [r.strip() for r in fh.readlines() if r.strip() and not r.startswith('#')]

setuptools.setup(
    name="django-signal-notification",  # Replace with your own username
    version="0.0.1",
    author="PProlancer",
    author_email="pprolancer@gmail.com",
    license="Apache License",
    description="django app to send notifications using signals",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords=["django", "notification", "signal"],
    url="https://github.com/pprolancer/django-signal-notification",
    packages=setuptools.find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    python_requires=">=3.4",
    install_requires=install_requires,
)
