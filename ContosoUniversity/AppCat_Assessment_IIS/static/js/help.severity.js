function getHelpSeverityPageContent() {
    const contentTemplate = 
`
<div style="max-width: 800px">
    <h5 style="margin-top: 40px" loc-text="WhatIsAnIssueSeverity">What is an issue severity?</h5>
    <p loc-text="IssueSeverityDescription1">In addition to the Story points, migration tasks is assigned a severity that indicates whether the task must be completed or can be postponed.</p>

    <h5 style="margin-top: 40px" loc-text="SeverityLevels">Severity levels</h5>
    <table class="table table-without-top-border">
        <thead>
            <tr>
                <th loc-text="SeverityLevel">Severity level</th>
                <th loc-text="Description">Description</th>
            </tr>
        </thead>
        <tr>
            <td loc-text="Information">Information</td>
            <td loc-text="InformationDescription">The issue was raised only for informational purpose and is not required to be resolved.</td>
        </tr>
        <tr>
            <td loc-text="Potential">Potential</td>
            <td loc-text="PotentialDescription">This issue may be blocking in some situations but not in others. These issues should be reviewed to determine whether a change is required or not. Potential issues often relate to external dependencies, for example, which are blocking if the dependency will not be accessible from Azure but will not be blocking if the dependency will be accessible.</td>
        </tr>
        <tr>
            <td loc-text="Optional">Optional</td>
            <td loc-text="OptionalDescription">The issue discovered is real issue fixing which could improve the app after migration, however it is not blocking, it could be resolved or not.</td>
        </tr>
        <tr>
            <td loc-text="Mandatory">Mandatory</td>
            <td loc-text="MandatoryDescription">The issue has to be resolved for the migration to be successful.</td>
        </tr>
    </table>
</div>
`;

    return {
        "content": contentTemplate
    };
}
