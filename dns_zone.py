import re 
import dns.query     
import dns.resolver  
import dns.update    

class DnsError(Exception):
    '''
    Custom exception class for DNS-related errors
    '''
    def __init__(self, message, status_code):
        self.message = message
        self.status_code = status_code

class DnsZone:
    def __init__ (self, zone, nameserver, timeout = 5.0):
        self.zone = re.sub('[.]$', '', zone)
        self.nameserver = nameserver
        self.resolver = dns.resolver.Resolver(configure=False)
        self.resolver.nameservers = [ self.nameserver ]
        self.timeout = timeout

    def _update(self, update_record):
        try:
            dns.query.udp(update_record, self.nameserver, timeout=self.timeout)
        except dns.exception.Timeout:
            raise DnsError(f'connection to nameserver {self.nameserver} timed out', 503)

    def can_contain(self, fqdn):
        return self.zone in fqdn

    def check_address(self, fqdn):
        try:
            return { 'ipv4' : self.resolver.resolve(fqdn, lifetime=self.timeout).response.answer[0][0].address , 'error' : False }
        except dns.exception.Timeout:
            raise DnsError(f'connection to nameserver {self.nameserver} timed out', 503)
        except dns.resolver.NXDOMAIN:
            raise DnsError(f'{fqdn} not found', 404)

    def update_address(self, fqdn, ipv4):
        if not self.can_contain(fqdn):
            raise DnsError(f'FQDN "{fqdn}" is not part of zone {self.zone}', 400)

        my_update = dns.update.Update(self.zone)
        my_update.replace(f'{fqdn}.', 300, 'a', ipv4)

        try:
            self._update(my_update)
        except DnsError:
            raise

        return self.check_address(fqdn)

    def clear_address(self, fqdn):
        if not self.can_contain(fqdn):
            raise DnsError(f'FQDN "{fqdn}" is not part of zone {self.zone}', 400)

        my_update = dns.update.Update(self.zone)
        my_update.delete(f'{fqdn}.')

        try:
            self._update(my_update)
        except DnsError:
            raise

        try:
            return { 'error' : True, 'error_text' : f'{fqdn} resolves to {self.resolver.resolve(fqdn).response.answer[0][0].address}' }
        except dns.resolver.NXDOMAIN:
            return { 'ipv4' : 'not found' }

    def add_address(self, fqdn, ipv4):
        if not self.can_contain(fqdn):
            raise DnsError(f'FQDN "{fqdn}" is not part of zone {self.zone}', 400)

        my_update = dns.update.Update(self.zone)
        my_update.add(f'{fqdn}.', 300, 'a', ipv4)

        try:
            self._update(my_update)
        except DnsError:
            raise

        return self.check_address(fqdn)