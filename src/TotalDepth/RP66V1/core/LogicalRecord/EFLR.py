"""
Implements the Explicitly Formatted Logical Record [RP66V1 Section 3 Logical Record Syntax]

References:
RP66V1: http://w3.energistics.org/rp66/v1/rp66v1.html
Specifically section 3: http://w3.energistics.org/rp66/v1/rp66v1_sec3.html
"""
# import collections
import typing

from TotalDepth.RP66V1 import ExceptionTotalDepthRP66V1
from TotalDepth.RP66V1.core.File import LogicalData
from TotalDepth.RP66V1.core.LogicalRecord.ComponentDescriptor import ComponentDescriptor
from TotalDepth.RP66V1.core.RepCode import IDENT, UVARI, USHORT, UNITS, code_read, OBNAME, ObjectName


class ExceptionEFLR(ExceptionTotalDepthRP66V1):
    pass


class ExceptionEFLRSet(ExceptionEFLR):
    pass


class ExceptionEFLRAttribute(ExceptionEFLR):
    pass


class ExceptionEFLRTemplate(ExceptionEFLR):
    pass


class ExceptionEFLRObject(ExceptionEFLR):
    pass


class Set:
    def __init__(self, ld: LogicalData):
        component_descriptor = ComponentDescriptor(ld.read())
        if not component_descriptor.is_set_group:
            raise ExceptionEFLRSet(f'Component Descriptor does not represent a set but a {component_descriptor.type}.')
        self.type = IDENT(ld)
        self.name = ComponentDescriptor.CHARACTERISTICS_AND_COMPONENT_FORMAT_SET_MAP['N'].global_default
        if component_descriptor.has_set_N:
            self.name = IDENT(ld)


class AttributeBase:
    def __init__(self, component_descriptor: ComponentDescriptor):
        if not component_descriptor.is_attribute_group:
            raise ExceptionEFLRAttribute(
                f'Component Descriptor does not represent a attribute but a {component_descriptor.type}.'
            )
        self.component_descriptor = component_descriptor
        self.label = ComponentDescriptor.CHARACTERISTICS_AND_COMPONENT_FORMAT_ATTRIBUTE_MAP['L'].global_default
        self.count = ComponentDescriptor.CHARACTERISTICS_AND_COMPONENT_FORMAT_ATTRIBUTE_MAP['C'].global_default
        self.rep_code = ComponentDescriptor.CHARACTERISTICS_AND_COMPONENT_FORMAT_ATTRIBUTE_MAP['R'].global_default
        self.units = ComponentDescriptor.CHARACTERISTICS_AND_COMPONENT_FORMAT_ATTRIBUTE_MAP['U'].global_default
        self.value = ComponentDescriptor.CHARACTERISTICS_AND_COMPONENT_FORMAT_ATTRIBUTE_MAP['V'].global_default

    def __eq__(self, other):
        if isinstance(other, AttributeBase):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __str__(self) -> str:
        return f'CD: {self.component_descriptor} L: {self.label} C: {self.count}' \
            f' R: {self.rep_code} U: {self.units} V: {self.value}'


class TemplateAttribute(AttributeBase):
    def __init__(self, component_descriptor: ComponentDescriptor, ld: LogicalData):
        super().__init__(component_descriptor)
        if self.component_descriptor.has_attribute_L:
            self.label = IDENT(ld)
        if self.component_descriptor.has_attribute_C:
            self.count = UVARI(ld)
        if self.component_descriptor.has_attribute_R:
            self.rep_code = USHORT(ld)
        if self.component_descriptor.has_attribute_U:
            self.units = UNITS(ld)
        if self.component_descriptor.has_attribute_V:
            self.value = [code_read(self.rep_code, ld) for _i in range(self.count)]


class Attribute(AttributeBase):
    def __init__(self,
                 component_descriptor: ComponentDescriptor,
                 ld: LogicalData,
                 template_attribute: TemplateAttribute,
                 ):
        super().__init__(component_descriptor)
        if self.component_descriptor.has_attribute_L:
            self.label = IDENT(ld)
        else:
            self.label = template_attribute.label
        if self.component_descriptor.has_attribute_C:
            self.count = UVARI(ld)
        else:
            self.count = template_attribute.count
        if self.component_descriptor.has_attribute_R:
            self.rep_code = USHORT(ld)
        else:
            self.rep_code = template_attribute.rep_code
        if self.component_descriptor.has_attribute_U:
            self.units = UNITS(ld)
        else:
            self.units = template_attribute.units
        if self.component_descriptor.has_attribute_V:
            self.value = [code_read(self.rep_code, ld) for _i in range(self.count)]
        else:
            self.value = template_attribute.value


class Template:
    def __init__(self, ld: LogicalData):
        self.attrs: typing.List[TemplateAttribute] = []
        while True:
            component_descriptor = ComponentDescriptor(ld.read())
            if not component_descriptor.is_attribute_group:
                raise ExceptionEFLRTemplate(f'Component Descriptor does not represent a attribute but a {component_descriptor.type}.')
            self.attrs.append(TemplateAttribute(component_descriptor, ld))
            next_component_descriptor = ComponentDescriptor(ld.peek())
            if next_component_descriptor.is_object:
                break

    def __len__(self) -> int:
        return len(self.attrs)

    def __getitem__(self, item) -> TemplateAttribute:
        return self.attrs[item]

    def __eq__(self, other) -> bool:
        if other.__class__ == Template:
            return self.attrs == other.attrs
        return NotImplemented


class Object:
    def __init__(self, ld: LogicalData, template: Template):
        component_descriptor = ComponentDescriptor(ld.read())
        if not component_descriptor.is_object:
            raise ExceptionEFLRObject(
                f'Component Descriptor does not represent a object but a {component_descriptor.type}.')
        self.name: ObjectName = OBNAME(ld)
        self.attrs: typing.List[typing.Union[AttributeBase, None]] = []
        index: int = 0
        while True:
            component_descriptor = ComponentDescriptor(ld.read())
            if not component_descriptor.is_attribute_group:
                raise ExceptionEFLRObject(f'Component Descriptor does not represent a attribute but a {component_descriptor.type}.')
            if template[index].component_descriptor.is_invariant_attribute:
                self.attrs.append(template[index])
            elif template[index].component_descriptor.is_absent_attribute:
                self.attrs.append(None)
            else:
                self.attrs.append(Attribute(component_descriptor, ld, template[index]))
                if ld.remain == 0 or ComponentDescriptor(ld.peek()).is_object:
                    break
                # next_component_descriptor = ComponentDescriptor(ld.peek())
                # if next_component_descriptor.is_object:
                #     break
            index += 1
        while len(self.attrs) < len(template):
            self.attrs.append(template[len(self.attrs)])
        if len(template) != len(self.attrs):
            raise ExceptionEFLRObject(
                f'Template specifies {len(template)} attributes but Logical Data has {len(self.attrs)}'
            )

    def __len__(self) -> int:
        return len(self.attrs)

    def __getitem__(self, item) -> typing.Union[AttributeBase, None]:
        return self.attrs[item]

    def __eq__(self, other) -> bool:
        if other.__class__ == Object:
            return self.name == other.name and self.attrs == other.attrs
        return NotImplemented


class ExplicitlyFormattedLogicalRecord:
    def __init__(self, ld: LogicalData):
        self.set: Set = Set(ld)
        self.template: Template = Template(ld)
        self.objects: typing.List[Object] = []
        while ld:
            self.objects.append(Object(ld, self.template))

    def __len__(self) -> int:
        return len(self.objects)

    def __getitem__(self, item) -> Object:
        return self.objects[item]


class IndirectlyFormattedLogicalRecord:
    def __init__(self, eflr: ExplicitlyFormattedLogicalRecord, ld: LogicalData):
        self.data_descriptor_reference = OBNAME(ld)
        # TODO: Indirectly Formatted Data

