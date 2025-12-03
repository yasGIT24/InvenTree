/**
 * Vendor Category management interface
 *
 * [AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation]
 * [AGENT GENERATED CODE - REQUIREMENT:Bulk Upload Vendor Categories with Validation]
 */

import { Trans, t } from '@lingui/macro';
import { Grid } from '@mui/material';

import { PageDetail } from '@app/components/nav/PageDetail';
import { AddIcon, FileIcon, ImportIcon } from '@app/components/Icons';
import { ActionButton } from '@app/components/buttons/ActionButton';
import { useCreateApiForm } from '@app/forms/ApiForm';
import { VendorCategoryTable } from '@app/tables/company/VendorCategoryTable';
import { apiUrl } from '@app/utils/urls';
import { useUserState } from '@app/states/UserState';
import { useImportDataModal } from '@app/components/modals/ImportData';

export default function VendorCategoriesPage() {
  const user = useUserState();
  const canAdd = user.hasPermission('company.add_vendorcategory');
  const canImport = user.hasPermission('company.add_vendorcategory');

  const newCategoryForm = useCreateApiForm({
    url: apiUrl('vendor-category-list'),
    title: t`Add Vendor Category`,
    fields: {
      parent: {},
      name: {
        label: t`Name`,
        required: true
      },
      description: {
        label: t`Description`
      }
    }
  });
  
  const importModal = useImportDataModal({
    modelName: 'vendorcategory',
  });

  return (
    <PageDetail
      title={t`Vendor Categories`}
      actions={[
        {
          icon: <AddIcon />,
          title: t`Add Vendor Category`,
          onClick: () => newCategoryForm.open({}),
          hidden: !canAdd
        },
        {
          icon: <ImportIcon />,
          title: t`Import Categories`,
          onClick: () => importModal.open(),
          hidden: !canImport
        }
      ]}
    >
      {newCategoryForm.renderer()}
      {importModal.renderer}
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <VendorCategoryTable />
        </Grid>
      </Grid>
    </PageDetail>
  );
}