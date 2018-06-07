from drydock_provisioner.orchestrator.validations.validators import Validators


class HugepagesValidity(Validators):
    def __init__(self):
        super().__init__('Hugepages', 'DD1008')

    def run_validation(self, site_design, orchestrator=None):
        """
        Ensures that if hugepages are specified in kernel params, that both
        size and count exist.
        """
        for baremetal_node in site_design.baremetal_nodes or []:
            if (('hugepages' in baremetal_node.kernel_params
                 and 'hugepagesz' not in baremetal_node.kernel_params)
                    or ('hugepages' not in baremetal_node.kernel_params
                        and 'hugepagesz' in baremetal_node.kernel_params)):
                self.report_error(
                    'Invalid hugepages kernel configuration',
                    [baremetal_node.doc_ref],
                    'hugepages and hugepagesz must be specified together')

        return
