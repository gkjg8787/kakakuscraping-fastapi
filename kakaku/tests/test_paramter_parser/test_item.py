import parameter_parser.item as ppi
from common import filter_name as fn
from common import templates_string


def test_get_extract_store_sort_list():
    for essn in fn.ExtractStoreSortName:
        fq = {
            fn.FilterQueryName.ESSORT.value: essn.id,
        }
        results = ppi.get_extract_store_sort_list(f=fq)
        for res in results:
            if res.id == essn.id:
                assert res.selected == templates_string.HTMLOption.SELECTED.value
                break


class TestExtractStoreFilterQuery:
    def test_convert_itemsort_to_essort(self):
        for isort in fn.ItemSortName:
            result = ppi.ExtractStoreFilterQuery.convert_itemsort_to_essort(isort.id)
            if isort == fn.ItemSortName.STORE_NAME:
                assert result is None
            else:
                assert result == isort.id

    def test_input_essort_query(self):
        for essn in fn.ExtractStoreSortName:
            fq = {ppi.FilterQueryName.ESSORT.value: str(essn.id)}
            esfq = ppi.ExtractStoreFilterQuery(**fq)
            result_fq = esfq.get_filter_dict()
            correct_fq = fq.copy()
            correct_fq.update(
                {ppi.FilterQueryName.ACT.value: str(ppi.ActFilterName.ACT.id)}
            )
            assert correct_fq == result_fq

    def test_input_itemsort_query(self):
        for isn in fn.ItemSortName:
            fq = {ppi.FilterQueryName.ISORT.value: str(isn.id)}
            esfq = ppi.ExtractStoreFilterQuery(**fq)
            result_fq = esfq.get_filter_dict()
            correct_fq = {ppi.FilterQueryName.ACT.value: str(ppi.ActFilterName.ACT.id)}
            if isn != fn.ItemSortName.STORE_NAME:
                correct_fq.update({ppi.FilterQueryName.ESSORT.value: str(isn.id)})

            assert correct_fq == result_fq
