using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using BaroqueUI;


public class TextHint : WorldObject
{
    public TextMesh textMesh;
    public Color nonSelectedColor, selectedColor;

    int ignore_controller_num = -1;

    private void Start()
    {
        var ct = Controller.HoverTracker(this);
        ct.onEnter += Ct_onEnter;
        ct.onLeave += Ct_onLeave;
        ct.onTouchDown += Ct_onDown;
        ct.onTriggerDown += Ct_onDown;
    }

    private void Ct_onDown(Controller controller)
    {
        //...;
    }

    private void Ct_onEnter(Controller controller)
    {
        var world = GetComponentInParent<WorldScript>();
        if (world.CheckController(controller, ignore_controller_num))
            return;

        textMesh.color = selectedColor;
    }

    private void Ct_onLeave(Controller controller)
    {
        textMesh.color = nonSelectedColor;
    }

    public override void UpdateWorldObject(float[] data)
    {
        int index = 0;
        textMesh.text = GetString(data, ref index);
        Vector3 p1 = GetVec3(data, index);
        Vector3 p2 = GetVec3(data, index + 3);
        ignore_controller_num = (int)data[index + 6];

        transform.localPosition = (p1 + p2) * 0.5f;

        Vector3 p12 = transform.parent.TransformVector(p2 - p1);
        Vector3 pos2head = Baroque.GetHeadTransform().position - transform.position;
        Vector3 upwards = Vector3.Cross(pos2head, p12);
        Vector3 forward = Vector3.Cross(upwards, p12);
        if (upwards.y < -1e-3)
            upwards = -upwards;
        if (forward != Vector3.zero)
            transform.rotation = Quaternion.LookRotation(forward, upwards);

        float s = transform.parent.localScale.y;
        transform.localScale = Vector3.one / s;
    }
}
