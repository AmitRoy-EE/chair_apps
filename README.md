# Apps of the [Chair of Energy Systems and Energy Economics](https://www.ee.ruhr-uni-bochum.de/index.html.en)

A collection of [streamlit](https://streamlit.io/) apps for the purposes of teaching and science communication.

It is currently hosted [here](https://apps.ee.rub.de/).

## Adding a page

Adding a page is rather easy. The required steps are as follows.

1) Add the repository that you want to share as a [submodule](https://git-scm.com/book/en/v2/Git-Tools-Submodules) to this repo. 
    * If your repository doesn't contain a streamlit app, create one.
2) Ensure that your app is wrapped inside a single `run()` function.
3) Add a page in the [pages](https://gitlab.ruhr-uni-bochum.de/ee/chair_apps/-/tree/main/pages?ref_type=heads) folder, which imports and executes this function. The existing pages may be used as inspiration.

## Tests

While unit tests are not actively developed, integration tests are in place, that ensure each page loads without error. They run upon merge request.



