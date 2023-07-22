from __future__ import annotations

from gi.repository import Gio

from gaphor import UML
from gaphor.core import transactional
from gaphor.diagram.propertypages import (
    LabelValue,
    unsubscribe_all_on_destroy,
    PropertyPageBase,
    PropertyPages,
    handler_blocking,
    new_resource_builder,
)
from gaphor.SysML import sysml
from gaphor.SysML.blocks.block import BlockItem
from gaphor.SysML.blocks.property import PropertyItem
from gaphor.SysML.blocks.proxyport import ProxyPortItem
from gaphor.SysML.requirements.requirement import RequirementItem
from gaphor.UML.classes.classespropertypages import AttributesPage, OperationsPage


new_builder = new_resource_builder("gaphor.SysML")


@PropertyPages.register(sysml.Requirement)
class RequirementPropertyPage(PropertyPageBase):
    order = 15

    def __init__(self, subject: sysml.Requirement):
        super().__init__()
        assert subject
        self.subject = subject
        self.watcher = subject.watcher()

    def construct(self):
        builder = new_builder(
            "requirement-editor",
            "requirement-text-buffer",
            signals={
                "requirement-id-changed": (self._on_id_changed,),
            },
        )
        subject = self.subject

        entry = builder.get_object("requirement-id")
        entry.set_text(subject.externalId or "")

        text_view = builder.get_object("requirement-text")

        buffer = builder.get_object("requirement-text-buffer")
        if subject.text:
            buffer.set_text(subject.text)

        @handler_blocking(buffer, "changed", self._on_text_changed)
        def text_handler(event):
            if not text_view.props.has_focus:
                buffer.set_text(event.new_value)

        self.watcher.watch("text", text_handler)

        return unsubscribe_all_on_destroy(
            builder.get_object("requirement-editor"), self.watcher
        )

    @transactional
    def _on_id_changed(self, entry):
        self.subject.externalId = entry.get_text()

    @transactional
    def _on_text_changed(self, buffer):
        self.subject.text = buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(), False
        )


PropertyPages.register(RequirementItem)(AttributesPage)
PropertyPages.register(RequirementItem)(OperationsPage)

PropertyPages.register(BlockItem)(OperationsPage)


@PropertyPages.register(BlockItem)
class CompartmentPage(PropertyPageBase):
    """An editor for Block items."""

    order = 30

    def __init__(self, item):
        super().__init__()
        self.item = item

    def construct(self):
        if not self.item.subject:
            return

        builder = new_builder(
            "compartment-editor",
            signals={
                "show-parts-changed": (self._on_show_parts_change,),
                "show-references-changed": (self._on_show_references_change,),
                "show-values-changed": (self._on_show_values_change,),
            },
        )

        show_parts = builder.get_object("show-parts")
        show_parts.set_active(self.item.show_parts)

        show_references = builder.get_object("show-references")
        show_references.set_active(self.item.show_references)

        show_values = builder.get_object("show-values")
        show_values.set_active(self.item.show_values)

        return builder.get_object("compartment-editor")

    @transactional
    def _on_show_parts_change(self, button, gparam):
        self.item.show_parts = button.get_active()

    @transactional
    def _on_show_references_change(self, button, gparam):
        self.item.show_references = button.get_active()

    @transactional
    def _on_show_values_change(self, button, gparam):
        self.item.show_values = button.get_active()


@PropertyPages.register(sysml.Property)
class PropertyAggregationPropertyPage(PropertyPageBase):
    """An editor for Properties (a.k.a.

    attributes).
    """

    order = 30

    AGGREGATION = ("none", "shared", "composite")

    def __init__(self, subject: sysml.Property):
        super().__init__()
        self.subject = subject

    def construct(self):
        if not self.subject or isinstance(self.subject, UML.Port):
            return

        builder = new_builder(
            "property-aggregation-editor",
            signals={
                "aggregation-changed": (self._on_aggregation_change,),
            },
        )

        aggregation = builder.get_object("aggregation")
        aggregation.set_selected(self.AGGREGATION.index(self.subject.aggregation))

        return builder.get_object("property-aggregation-editor")

    @transactional
    def _on_aggregation_change(self, combo, _pspec):
        self.subject.aggregation = self.AGGREGATION[combo.get_selected()]


@PropertyPages.register(PropertyItem)
@PropertyPages.register(ProxyPortItem)
class PropertyTypePropertyPage(PropertyPageBase):
    order = 31

    def __init__(self, item):
        super().__init__()
        self.item = item

    def construct(self):
        if not self.item.subject:
            return

        builder = new_builder(
            "property-type-editor",
            signals={
                "show-type-changed": (self._on_show_type_change,),
            },
        )

        dropdown = builder.get_object("property-type")
        model = list_of_classifiers(self.item.subject.model)
        dropdown.set_model(model)

        if self.item.subject.type:
            dropdown.set_selected(
                next(
                    n
                    for n, lv in enumerate(model)
                    if lv.value == self.item.subject.type.id
                )
            )

        dropdown.connect("notify::selected", self._on_property_type_changed)

        if isinstance(self.item.subject, UML.Port):
            show_type = builder.get_object("show-type")
            show_type.set_active(self.item.show_type)
        else:
            builder.get_object("type-toggle-box").unparent()

        return builder.get_object("property-type-editor")

    @transactional
    def _on_property_type_changed(self, dropdown, _pspec):
        subject = self.item.subject
        if id := dropdown.get_selected_item().value:
            element = subject.model.lookup(id)
            assert isinstance(element, UML.Type)
            subject.type = element
        else:
            del subject.type

    @transactional
    def _on_show_type_change(self, button, _gparam):
        self.item.show_type = button.get_active()


@PropertyPages.register(UML.Association)
@PropertyPages.register(sysml.Connector)
class ItemFlowPropertyPage(PropertyPageBase):
    """Item Flow on Connectors."""

    order = 35

    def __init__(self, subject: UML.Association | sysml.Connector):
        super().__init__()
        self.subject = subject

    @property
    def information_flow(self):
        subject = self.subject
        if isinstance(subject, sysml.Connector):
            iflows = subject.informationFlow
        elif isinstance(subject, UML.Relationship):
            iflows = subject.abstraction
        return iflows[0] if iflows else None

    def construct(self):
        if not self.subject:
            return

        builder = new_builder(
            "item-flow-editor",
            signals={
                "item-flow-active": (self._on_item_flow_active,),
                "item-flow-name-changed": (self._on_item_flow_name_changed,),
                "invert-direction-changed": (self._invert_direction_changed,),
            },
        )

        use_flow = builder.get_object("use-item-flow")
        self.entry = builder.get_object("item-flow-name")

        dropdown = builder.get_object("item-flow-type")
        model = list_of_classifiers(self.subject.model)
        dropdown.set_model(model)

        use_flow.set_active(isinstance(self.information_flow, sysml.ItemFlow))
        use_flow.set_sensitive(
            not (
                self.information_flow
                and type(self.information_flow) is UML.InformationFlow
            )
        )
        self.entry.set_sensitive(use_flow.get_active())
        if (iflow := self.information_flow) and iflow.itemProperty:
            assert isinstance(iflow, sysml.ItemFlow)
            self.entry.set_text(iflow.itemProperty.name or "")
            if iflow.itemProperty.type:
                dropdown.set_selected(
                    next(
                        n
                        for n, lv in enumerate(model)
                        if lv.value == iflow.itemProperty.type.id
                    )
                )

        dropdown.connect("notify::selected", self._on_item_flow_type_changed)

        return builder.get_object("item-flow-editor")

    @transactional
    def _on_item_flow_active(self, switch, gparam):
        active = switch.get_active()
        subject = self.subject
        iflow = self.information_flow
        if active and not iflow:
            if isinstance(subject, sysml.Connector):
                subject.informationFlow = create_item_flow(subject)
            elif isinstance(subject, UML.Relationship):
                subject.abstraction = create_item_flow(subject)
        elif not active and iflow:
            iflow.unlink()
        self.entry.set_sensitive(switch.get_active())
        self.entry.set_text("")

    @transactional
    def _on_item_flow_name_changed(self, entry):
        if not (iflow := self.information_flow):
            return

        assert isinstance(iflow, sysml.ItemFlow)
        iflow.itemProperty.name = entry.get_text()

    @transactional
    def _on_item_flow_type_changed(self, dropdown, _pspec):
        if not (iflow := self.information_flow):
            return

        assert isinstance(iflow, sysml.ItemFlow)
        if id := dropdown.get_selected_item().value:
            element = self.subject.model.lookup(id)
            assert isinstance(element, UML.Type)
            iflow.itemProperty.type = element
        else:
            del iflow.itemProperty.type

    @transactional
    def _invert_direction_changed(self, button):
        if not (iflow := self.information_flow):
            return

        iflow.informationSource, iflow.informationTarget = (
            iflow.informationTarget,
            iflow.informationSource,
        )


def list_of_classifiers(element_factory):
    model = Gio.ListStore.new(LabelValue)
    model.append(LabelValue("", None))
    for c in sorted(
        (c for c in element_factory.select(UML.Classifier) if c.name),
        key=lambda c: c.name or "",
    ):
        model.append(LabelValue(c.name, c.id))
    return model


def create_item_flow(subject: UML.Association | sysml.Connector) -> sysml.ItemFlow:
    iflow = subject.model.create(sysml.ItemFlow)
    if isinstance(subject, sysml.Connector):
        iflow.informationSource = subject.end[0].role
        iflow.informationTarget = subject.end[1].role
    elif isinstance(subject, UML.Relationship):
        iflow.informationSource = subject.memberEnd[0]
        iflow.informationTarget = subject.memberEnd[1]
    iflow.itemProperty = subject.model.create(sysml.Property)
    return iflow
