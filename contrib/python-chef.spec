%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%global pkgname chef

Name:		python-%{pkgname}
Version:	0.2.1
Release:	1%{?dist}
Summary:	A Python API for interacting with a Chef server

Group:		Development/Libraries
License:	BSD
URL:		http://github.com/coderanger/pychef
Source0:	coderanger-pychef-v0.2.1-0-g5b9a185.tar.gz
BuildRoot:	%(mktemp -ud %{_tmppath}/%{name}-%{version}-%{release}-XXXXXX)

Requires:	    python openssl-devel
BuildRequires:	python python-devel python-setuptools

%description
A Python API for interacting with a Chef server.


%prep
%setup -q -n coderanger-pychef-g5b9a185


%build
%{__python} setup.py build


%install
rm -rf %{buildroot}

PATH=$PATH:%{buildroot}%{python_sitelib}/%{pkgname}
%{__python} setup.py install --root=%{buildroot}


%clean
rm -rf %{buildroot}


%files
%defattr(-,root,root,-)
#%doc
%dir %{python_sitelib}/PyChef-0.2.1-py2.6.egg-info/
%{python_sitelib}/PyChef-0.2.1-py2.6.egg-info/*
%dir %{python_sitelib}/%{pkgname}/
%{python_sitelib}/%{pkgname}/*.py
%{python_sitelib}/%{pkgname}/*.pyc
%{python_sitelib}/%{pkgname}/*.pyo
%dir %{python_sitelib}/%{pkgname}/tests/
%{python_sitelib}/%{pkgname}/tests/*.py
%{python_sitelib}/%{pkgname}/tests/*.pyc
%{python_sitelib}/%{pkgname}/tests/*.pyo
%dir %{python_sitelib}/%{pkgname}/utils/
%{python_sitelib}/%{pkgname}/utils/*.py
%{python_sitelib}/%{pkgname}/utils/*.pyc
%{python_sitelib}/%{pkgname}/utils/*.pyo


%changelog
* Tue Jul 26 2011 Daniel Aharon <daharon@sazze.com> - 0.2-1
- Initial release
