from .filing import Filing
from .standardizer import Standardizer
from .sked_dict_reader import SkedDictReader
# from .log_utils import configure_logging
from .type_utils import listType

from .settings import WORKING_DIRECTORY, ALLOWED_VERSIONSTRINGS


class XMLRunner(object):
    """ Load a Standardizer just a once while running multiple filings
        Return Filing objects with results, keyerrors set
    """
    def __init__(self, documentation=False, standardizer=None):
        self.documentation = documentation

        if documentation:
            # we need a new standardizer, ignore one if passed in
            self.standardizer = Standardizer(documentation=documentation)
        else:
            if standardizer:
                self.standardizer = standardizer
            else:
                self.standardizer = Standardizer()
        self.group_dicts = self.standardizer.get_groups()
        self.whole_filing_data = []
        self.filing_keyerr_data = []

    def get_standardizer(self):
        return self.standardizer

    def _run_schedule_k(self, sked, object_id, sked_dict, path_root, ein):
        assert sked == 'IRS990ScheduleK'
        if type(sked_dict) == listType:
            for individual_sked in sked_dict:
                doc_id = individual_sked['@documentId']
                reader = SkedDictReader(
                    self.standardizer,
                    self.group_dicts,
                    object_id,
                    ein,
                    documentId=doc_id,
                    documentation=self.documentation
                )

                result = reader.parse(individual_sked, parent_path=path_root)
                self.whole_filing_data.append({
                    'schedule_name': sked,
                    'groups': result['groups'],
                    'schedule_parts': result['schedule_parts']
                })
        else:
            reader = SkedDictReader(
                self.standardizer,
                self.group_dicts,
                object_id,
                ein,
                documentation=self.documentation)

            result = reader.parse(sked_dict, parent_path=path_root)
            self.whole_filing_data.append({
                'schedule_name': sked,
                'groups': result['groups'],
                'schedule_parts': result['schedule_parts']
            })

    def _run_schedule(self, sked, object_id, sked_dict, ein):
        path_root = "/" + sked
        # Only sked K (bonds) is allowed to repeat
        if sked == 'IRS990ScheduleK':
            self._run_schedule_k(sked, object_id, sked_dict, path_root, ein)

        else:
            reader = SkedDictReader(
                self.standardizer,
                self.group_dicts,
                object_id,
                ein,
                documentation=self.documentation
            )
            if sked == 'ReturnHeader990x':
                path_root = "/ReturnHeader"
            result = reader.parse(sked_dict, parent_path=path_root)
            self.whole_filing_data.append({
                'schedule_name': sked,
                'groups': result['groups'],
                'schedule_parts': result['schedule_parts']
            })

            if len(result['group_keyerrors']) > 0 or len(result['keyerrors'])> 0:
                self.filing_keyerr_data.append({
                    'schedule_name': sked,
                    'group_keyerrors':result['group_keyerrors'],
                    'keyerrors':result['keyerrors']
                })

    def run_filing(self, object_id, verbose=False):
        self.whole_filing_data = []
        self.filing_keyerr_data = []
        this_filing = Filing(object_id)
        this_filing.process(verbose=verbose)
        this_version = this_filing.get_version()
        if this_version in ALLOWED_VERSIONSTRINGS:
            this_version = this_filing.get_version()
            schedules = this_filing.list_schedules()
            ein = this_filing.get_ein()
            self.whole_filing_data = []
            for sked in schedules:
                sked_dict = this_filing.get_schedule(sked)
                self._run_schedule(sked, object_id, sked_dict, ein)

            this_filing.set_result(self.whole_filing_data)
            this_filing.set_keyerrors(self.filing_keyerr_data)
            return this_filing
        else:
            return this_filing

    def run_from_filing_obj(self, this_filing, verbose=False):  
        """
         Run from a pre-created filing object.
        """
        self.whole_filing_data = []
        self.filing_keyerr_data = []
        this_filing.process(verbose=verbose)
        object_id = this_filing.get_object_id()
        this_version = this_filing.get_version()
        if this_version in ALLOWED_VERSIONSTRINGS:
            this_version = this_filing.get_version()
            schedules = this_filing.list_schedules()
            ein = this_filing.get_ein()
            for sked in schedules:
                sked_dict = this_filing.get_schedule(sked)
                self._run_schedule(sked, object_id, sked_dict, ein)
            this_filing.set_result(self.whole_filing_data)
            this_filing.set_keyerrors(self.filing_keyerr_data)
            return this_filing
        else:
            return this_filing


    def run_sked(self, object_id, sked, verbose=False):
        """
        sked is the proper name of the schedule:
        IRS990, IRS990EZ, IRS990PF, IRS990ScheduleA, etc.
        """
        self.whole_filing_data = []
        self.filing_keyerr_data = []
        this_filing = Filing(object_id)
        this_filing.process(verbose=verbose)
        this_version = this_filing.get_version()
        if this_version in ALLOWED_VERSIONSTRINGS:
            this_version = this_filing.get_version()
            ein = this_filing.get_ein()
            sked_dict = this_filing.get_schedule(sked)
            self._run_schedule(sked, object_id, sked_dict, ein)

            this_filing.set_result(self.whole_filing_data)
            this_filing.set_keyerrors(self.filing_keyerr_data)
            return this_filing
        else:
            return this_filing