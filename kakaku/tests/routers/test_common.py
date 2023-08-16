from pydantic import BaseModel

def is_html(text):
    assert '<!DOCTYPE html>' in text
    assert '<head>' in text
    assert '</head>' in text
    assert '<body>' in text
    assert '</body' in text
    assert '</html>' in text

class RedirectCheckValue(BaseModel):
    status_code :int
    location :str

    def check_value(self, res):
        assert res.status_code == self.status_code
        assert self.location in res.headers["Location"]


def check_redirect(res, check_value :list[RedirectCheckValue]):
    assert len(res.history) == len(check_value)
    for i, r in enumerate(res.history):
        check_value[i].check_value(r)