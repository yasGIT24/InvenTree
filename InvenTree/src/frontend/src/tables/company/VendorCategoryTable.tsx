/**
 * Vendor Category Table
 *
 * Display a hierarchical table of vendor categories
 *
 * [AGENT GENERATED CODE - REQUIREMENT:Delete Vendor Categories with Validation]
 * [AGENT GENERATED CODE - REQUIREMENT:Bulk Upload Vendor Categories with Validation]
 */

import { t } from '@lingui/macro';
import { useMemo } from 'react';

import { AddIcon, PencilIcon, TrashIcon } from '@app/components/Icons';
import { ActionDropdown } from '@app/components/actions/ActionDropdown';
import { ActionGroup } from '@app/components/actions/ActionGroup';
import { DetailsButton } from '@app/components/buttons/DetailsButton';
import { useCreateApiForm } from '@app/forms/ApiForm';
import { TreeTable } from '@app/tables/TreeTable';
import { apiUrl } from '@app/utils/urls';

import { useTable } from '@app/hooks/UseTable';
import { useUserState } from '@app/states/UserState';

export default function VendorCategoryTable() {
  const table = useTable('vendorcategory');

  const user = useUserState();

  const tableColumns = useMemo(() => {
    return [
      {
        accessor: 'name',
        Header: t`Name`,
        className: 'text-nowrap'
      },
      {
        accessor: 'description',
        Header: t`Description`,
        className: 'text-nowrap'
      },
      {
        accessor: 'company_count',
        Header: t`Companies`,
        className: 'text-nowrap',
        sortable: true
      },
      {
        accessor: 'actions',
        width: 100,
        Header: t`Actions`,
        formatter: (record: any) => {
          const canEdit = user.hasPermission('company.change_vendorcategory');
          const canDelete = user.hasPermission('company.delete_vendorcategory') && !record.in_use;

          return (
            <ActionGroup>
              <DetailsButton
                model="vendorcategory"
                pk={record.pk}
                disabled={!canEdit}
              >
                <PencilIcon title={t`Edit Vendor Category`} />
              </DetailsButton>
              <ActionDropdown
                disabled={!canDelete}
                actions={[
                  {
                    name: 'delete',
                    icon: <TrashIcon />,
                    title: t`Delete Category`,
                    tooltip: record.in_use ? t`Cannot delete category while it is in use` : t`Delete vendor category`,
                    permission: canDelete,
                    onClick: () => {
                      if (canDelete) {
                        table.removeRecord(record.pk);
                      }
                    }
                  }
                ]}
              />
            </ActionGroup>
          );
        }
      }
    ];
  }, [table, user]);

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
    },
    onSuccess: () => {
      table.refreshTable();
    }
  });

  const addCategoryButton = useMemo(() => {
    if (user.hasPermission('company.add_vendorcategory')) {
      return {
        icon: <AddIcon />,
        title: t`Add Vendor Category`,
        onClick: () => newCategoryForm.open({})
      };
    } else {
      return undefined;
    }
  }, [user]);

  return (
    <>
      {newCategoryForm.renderer()}
      <TreeTable
        url={apiUrl('vendor-category-list')}
        tableState={table}
        columns={tableColumns}
        parentField="parent"
        defaultSort="name"
        tableFilters={{}}
        addButton={addCategoryButton}
        batchDeleteMode="none"
        params={{
          include_self: true
        }}
      />
    </>
  );
}