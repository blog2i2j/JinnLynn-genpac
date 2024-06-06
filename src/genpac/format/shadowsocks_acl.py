from ..util import Namespace
from .base import formater, FmtBase
from .ip import FmtIP

_TPL_DEF = '''
#! __GENPAC__
#! Generated: __GENERATED__
#! GFWList: __GFWLIST_DETAIL__
[bypass_all]

[proxy_list]
__GFWED_RULES__
'''

_TPL_GEOCN = '''
#! __GENPAC__
#! Generated: __GENERATED__
#! GFWList: __GFWLIST_DETAIL__
[proxy_all]

[bypass_list]
__CNIPS__
'''


@formater('ssacl', desc='Shadowsocks访问控制列表.')
class FmtSSACL(FmtBase):
    def __init__(self, *args, **kwargs):
        super(FmtSSACL, self).__init__(*args, **kwargs)

        if self.options.ssacl_geocn:
            self.options.gfwlist_disabled = True

    @classmethod
    def arguments(cls, parser):
        group = super(FmtSSACL, cls).arguments(parser)
        group.add_argument(
            '--ssacl-geocn', action='store_true',
            help='国内IP不走代理，所有国外IP走代理')
        return group

    @classmethod
    def config(cls, options):
        options['ssacl-geocn'] = {'default': False}

    @property
    def tpl(self):
        return _TPL_GEOCN if self.options.ssacl_geocn else _TPL_DEF

    def generate(self, replacements):
        return self.gen_by_geoip(replacements) if self.options.ssacl_geocn else \
            self.gen_by_gfwlist(replacements)

    def gen_by_gfwlist(self, replacements):
        def parse_rules(rules):
            rules = [r.replace('.', '\\.') for r in rules]
            rules = [f'(^|\\.){r}$' for r in rules]
            return rules

        gfwed_rules = parse_rules(self.gfwed_domains)

        replacements.update({
            '__GFWED_RULES__': '\n'.join(gfwed_rules)})

        return self.replace(self.tpl, replacements)

    def gen_by_geoip(self, replacements):
        ip_data = []
        for ip in self.fetch_cnips():
            ip_data.append(ip)
        replacements.update({
            '__CNIPS__': '\n'.join(ip_data)})
        return self.replace(self.tpl, replacements)

    def fetch_cnips(self):
        gen_ip = FmtIP(generator=self.generator, options=Namespace(ip_family='4', ip_cc='cn'))
        yield from gen_ip._fetch_data_cn(4)
